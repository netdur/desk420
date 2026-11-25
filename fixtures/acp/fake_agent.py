#!/usr/bin/env python3
"""Fake ACP agent for Desk420 tests.

Replays recorded Grok ACP fixtures or runs deterministic test scenarios
(cancel, crash-once, concurrent sessions) over stdio without network or credits.
"""

import argparse
import json
import os
import sys
import threading
import time

stdout_lock = threading.Lock()


def send_msg(msg):
    line = json.dumps(msg, separators=(",", ":"))
    with stdout_lock:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()


def read_msg():
    line = sys.stdin.readline()
    if not line:
        return None
    line = line.strip()
    if not line:
        return None
    return json.loads(line)


def default_init_result():
    return {
        "protocolVersion": 1,
        "agentCapabilities": {
            "loadSession": True,
            "promptCapabilities": {
                "image": True,
                "audio": False,
                "embeddedContext": True,
            },
            "mcpCapabilities": {"http": True, "sse": True},
            "sessionCapabilities": {"list": {}, "resume": {}, "close": {}},
        },
        "authMethods": [{"id": "grok.com", "name": "Grok"}],
    }


def run_cancel_mode():
    cancel_events = {}
    sess_counter = [0]

    def stream_turn(req_id, sid):
        ev = threading.Event()
        cancel_events[sid] = ev
        for i in range(200):
            if ev.is_set():
                send_msg({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"stopReason": "cancelled"},
                })
                return
            send_msg({
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "content": {"type": "text", "text": f"chunk-{i} "},
                    },
                },
            })
            time.sleep(0.015)
        send_msg({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"stopReason": "end_turn"},
        })

    while True:
        msg = read_msg()
        if msg is None:
            break
        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "initialize":
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": default_init_result()})
        elif method == "session/new":
            sess_counter[0] += 1
            sid = f"cancel-sess-{sess_counter[0]}"
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"sessionId": sid, "configOptions": []}})
        elif method == "session/prompt":
            sid = params.get("sessionId", "")
            t = threading.Thread(target=stream_turn, args=(req_id, sid), daemon=True)
            t.start()
        elif method == "session/cancel":
            sid = params.get("sessionId", "")
            ev = cancel_events.get(sid)
            if ev is not None:
                ev.set()
        elif req_id is not None:
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {}})


def run_crash_once_mode(marker_path):
    sess_counter = [0]
    while True:
        msg = read_msg()
        if msg is None:
            break
        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "initialize":
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": default_init_result()})
            if marker_path and not os.path.exists(marker_path):
                with open(marker_path, "w") as f:
                    f.write("crashed\n")
                time.sleep(0.02)
                sys.exit(1)
        elif method == "session/new":
            sess_counter[0] += 1
            sid = f"recovered-sess-{sess_counter[0]}"
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"sessionId": sid, "configOptions": []}})
        elif method == "session/prompt":
            sid = params.get("sessionId", "")
            send_msg({
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "content": {"type": "text", "text": "recovered-ok"},
                    },
                },
            })
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"stopReason": "end_turn"}})
        elif req_id is not None:
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {}})


def run_concurrent_mode():
    sess_counter = [0]
    threads = []

    def run_turn(req_id, sid, prompt_text):
        for i in range(5):
            send_msg({
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "content": {"type": "text", "text": f"{prompt_text}:{i};"},
                    },
                },
            })
            time.sleep(0.01)
        send_msg({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"stopReason": "end_turn", "_meta": {"totalTokens": 10, "inputTokens": 5, "modelId": "fake"}},
        })

    while True:
        msg = read_msg()
        if msg is None:
            break
        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "initialize":
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": default_init_result()})
        elif method == "session/new":
            sess_counter[0] += 1
            sid = f"conc-sess-{sess_counter[0]}"
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"sessionId": sid, "configOptions": []}})
        elif method == "session/prompt":
            sid = params.get("sessionId", "")
            prompt_text = ""
            blocks = params.get("prompt") or []
            if blocks and isinstance(blocks[0], dict):
                prompt_text = blocks[0].get("text", "")
            t = threading.Thread(target=run_turn, args=(req_id, sid, prompt_text), daemon=True)
            t.start()
            threads.append(t)
        elif req_id is not None:
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {}})

    for t in threads:
        t.join(timeout=2.0)


def run_fixture_mode(fixture_path, delay_ms):
    records = []
    with open(fixture_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    id_map = {}
    idx = 0
    n = len(records)

    while idx < n:
        rec = records[idx]
        d = rec["dir"]
        msg = rec["msg"]
        idx += 1

        if d == ">":
            incoming = read_msg()
            if incoming is None:
                return
            if "id" in msg and "id" in incoming:
                id_map[msg["id"]] = incoming["id"]
        else:
            out = dict(msg)
            if "method" not in out and "id" in out and out["id"] in id_map:
                out["id"] = id_map[out["id"]]
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)
            send_msg(out)


def run_sessions_mode():
    sessions = [
        {
            "sessionId": "hist-1",
            "cwd": "/work/desk420",
            "title": "Plan Japan trip",
            "updatedAt": "2026-11-22T15:00:00Z",
            "history": [
                ("user", "Help me plan a 5-day Kyoto itinerary."),
                ("agent", "Here is a relaxed 5-day Kyoto plan covering Arashiyama, Fushimi Inari, and Gion."),
            ],
        },
        {
            "sessionId": "hist-2",
            "cwd": "/work/desk420",
            "title": "Summarize quarterly report",
            "updatedAt": "2026-11-22T14:00:00Z",
            "history": [
                ("user", "Summarize the key points from Q4."),
                ("agent", "Revenue grew 18% YoY and retention reached 94%."),
            ],
        },
    ]
    sess_counter = [2]

    while True:
        msg = read_msg()
        if msg is None:
            break
        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}

        if method == "initialize":
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": default_init_result()})
        elif method == "session/list":
            out = [
                {"sessionId": s["sessionId"], "cwd": s["cwd"], "title": s["title"], "updatedAt": s["updatedAt"]}
                for s in sessions
            ]
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"sessions": out}})
        elif method == "session/load":
            sid = params.get("sessionId", "")
            found = next((s for s in sessions if s["sessionId"] == sid), None)
            if found:
                for role, txt in found["history"]:
                    su = "user_message_chunk" if role == "user" else "agent_message_chunk"
                    send_msg({
                        "jsonrpc": "2.0",
                        "method": "session/update",
                        "params": {
                            "sessionId": sid,
                            "update": {"sessionUpdate": su, "content": {"type": "text", "text": txt}},
                        },
                    })
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"configOptions": []}})
        elif method == "session/new":
            sess_counter[0] += 1
            sid = f"hist-{sess_counter[0]}"
            cwd = params.get("cwd", "/tmp")
            sessions.insert(0, {
                "sessionId": sid,
                "cwd": cwd,
                "title": "New conversation",
                "updatedAt": "2026-11-22T17:00:00Z",
                "history": [],
            })
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"sessionId": sid, "configOptions": []}})
        elif method == "session/prompt":
            sid = params.get("sessionId", "")
            blocks = params.get("prompt") or []
            user_txt = blocks[0].get("text", "") if blocks else ""
            reply = f"Echo from Grok: {user_txt}"
            found = next((s for s in sessions if s["sessionId"] == sid), None)
            if found:
                found["history"].append(("user", user_txt))
                found["history"].append(("agent", reply))
                found["title"] = user_txt[:40]
            send_msg({
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {"sessionUpdate": "agent_message_chunk", "content": {"type": "text", "text": reply}},
                },
            })
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"stopReason": "end_turn"}})
        elif method == "_x.ai/session/search":
            q = (params.get("query") or "").lower()
            hits = []
            for s in sessions:
                blob = s["title"].lower() + " " + " ".join(t.lower() for _, t in s["history"])
                if q and q in blob:
                    hits.append({"sessionId": s["sessionId"], "cwd": s["cwd"], "summary": s["title"], "score": 1.0})
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"results": hits}})
        elif method == "_x.ai/session/rename":
            sid = params.get("sessionId", "")
            title = params.get("title", "")
            for s in sessions:
                if s["sessionId"] == sid:
                    s["title"] = title
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"success": True}})
        elif method == "_x.ai/session/delete":
            sid = params.get("sessionId", "")
            sessions[:] = [s for s in sessions if s["sessionId"] != sid]
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"success": True}})
        elif req_id is not None:
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {}})


def run_agent_mode(listed=False):
    config_options = [
        {
            "id": "model",
            "name": "Model",
            "category": "model",
            "type": "select",
            "currentValue": "grok-4.7",
            "options": [
                {"value": "grok-4.7", "name": "Grok 4.7"},
                {"value": "grok-4.7-build-fast", "name": "Grok 4.7 Fast"},
                {"value": "grok-4.6", "name": "Grok 4.6"},
            ],
        },
        {
            "id": "reasoning_effort",
            "name": "Reasoning Effort",
            "category": "thought_level",
            "type": "select",
            "currentValue": "high",
            "options": [
                {"value": "xhigh", "name": "Extra High"},
                {"value": "high", "name": "High"},
                {"value": "medium", "name": "Medium"},
                {"value": "low", "name": "Low"},
            ],
        },
    ]
    perm_replies = {}
    perm_events = {}
    sess_counter = [0]
    # `desk` mode: session/list answers with what exists, so the sidebar,
    # Home's needs-you cards and its project grid have something to show.
    known = []
    if listed:
        known = [
            {"sessionId": "seed-1", "cwd": "/work/C+", "title": "cplus-core Memory Model Deep dive", "updatedAt": "2026-11-23T10:00:00Z"},
            {"sessionId": "seed-2", "cwd": "/work/sample-b", "title": "Inquiring About AI Visual Capabilities", "updatedAt": "2026-11-23T09:00:00Z"},
            {"sessionId": "seed-3", "cwd": "/work/sample-c", "title": "Sample Web App landing page", "updatedAt": "2026-11-23T08:00:00Z"},
        ]

    def run_agent_turn(req_id, sid, prompt_txt):
        send_msg({
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": sid,
                "update": {
                    "sessionUpdate": "agent_thought_chunk",
                    "content": {"type": "text", "text": "Checking files and preparing edit."},
                },
            },
        })
        # SearchTool noise (should be hidden in UI)
        send_msg({
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": sid,
                "update": {
                    "sessionUpdate": "tool_call",
                    "toolCallId": "tc-search",
                    "title": "search_tool",
                    "kind": "other",
                    "status": "completed",
                    "rawOutput": {"type": "SearchTool", "content": "{}"},
                },
            },
        })
        # Edit tool call with diff
        send_msg({
            "jsonrpc": "2.0",
            "method": "session/update",
            "params": {
                "sessionId": sid,
                "update": {
                    "sessionUpdate": "tool_call",
                    "toolCallId": "tc-edit-1",
                    "title": "Edit `notes.txt`",
                    "kind": "edit",
                    "status": "completed",
                    "content": [{"type": "diff", "path": "/tmp/notes.txt", "oldText": "old line", "newText": "new line"}],
                    "rawOutput": {"type": "SearchReplace", "EditsApplied": {"old_string": "old line", "new_string": "new line"}},
                },
            },
        })
        # Permission request for bash rm command
        perm_rpc_id = 700 + sess_counter[0]
        ev = threading.Event()
        perm_events[perm_rpc_id] = ev
        send_msg({
            "jsonrpc": "2.0",
            "id": perm_rpc_id,
            "method": "session/request_permission",
            "params": {
                "sessionId": sid,
                "toolCall": {
                    "toolCallId": "tc-rm-1",
                    "kind": "execute",
                    "title": "Execute `rm temp.txt`",
                    "rawInput": {"variant": "Bash", "command": "rm temp.txt", "description": "Remove temp.txt"},
                },
                "options": [
                    {"optionId": "allow-once", "kind": "allow_once", "name": "Yes, proceed"},
                    {"optionId": "reject-once", "kind": "reject_once", "name": "No, reject"},
                ],
            },
        })
        ev.wait(timeout=600.0 if listed else 15.0)
        chosen = perm_replies.get(perm_rpc_id, "reject-once")
        if chosen.startswith("allow"):
            send_msg({
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "tool_call",
                        "toolCallId": "tc-rm-1",
                        "title": "Execute `rm temp.txt`",
                        "kind": "execute",
                        "status": "completed",
                        "rawOutput": {"type": "Bash", "output_for_prompt": "removed temp.txt\n", "exit_code": 0},
                    },
                },
            })
            send_msg({
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "agent_message_chunk",
                        "content": {"type": "text", "text": "Done! Updated notes.txt and removed temp.txt."},
                    },
                },
            })
            send_msg({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "stopReason": "end_turn",
                    "_meta": {"totalTokens": 420, "inputTokens": 300, "modelId": config_options[0]["currentValue"]},
                },
            })
        else:
            send_msg({
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "tool_call",
                        "toolCallId": "tc-rm-1",
                        "title": "Execute `rm temp.txt`",
                        "kind": "execute",
                        "status": "failed",
                        "_meta": {"toolNotRun": "rejected"},
                    },
                },
            })
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"stopReason": "cancelled"}})

    while True:
        msg = read_msg()
        if msg is None:
            break
        # Check if this is a response to our permission request
        if "method" not in msg and "id" in msg:
            rid = msg["id"]
            opt = ((msg.get("result") or {}).get("outcome") or {}).get("optionId", "reject-once")
            perm_replies[rid] = opt
            ev = perm_events.get(rid)
            if ev is not None:
                ev.set()
            continue

        method = msg.get("method")
        req_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "initialize":
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": default_init_result()})
        elif method == "session/list":
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"sessions": known}})
        elif method == "session/load":
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"configOptions": config_options}})
        elif method == "session/new":
            sess_counter[0] += 1
            sid = f"agent-sess-{sess_counter[0]}"
            if listed:
                known.insert(0, {"sessionId": sid, "cwd": params.get("cwd", "/tmp"),
                                 "title": "Update notes and clean up", "updatedAt": "2026-11-23T11:00:00Z"})
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"sessionId": sid, "configOptions": config_options}})
            send_msg({
                "jsonrpc": "2.0",
                "method": "session/update",
                "params": {
                    "sessionId": sid,
                    "update": {
                        "sessionUpdate": "available_commands_update",
                        "availableCommands": [
                            {"name": "compact", "description": "Compress conversation history", "input": None},
                            {"name": "deep-research", "description": "Deep web research", "input": {"hint": "topic"}},
                            {"name": "context", "description": "Show context usage", "input": None},
                        ],
                    },
                },
            })
        elif method == "session/set_config_option":
            cid = params.get("configId", "")
            val = params.get("value", "")
            for co in config_options:
                if co["id"] == cid:
                    co["currentValue"] = val
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"configOptions": config_options}})
        elif method == "session/prompt":
            sid = params.get("sessionId", "")
            blocks = params.get("prompt") or []
            txt = blocks[0].get("text", "") if blocks else ""
            t = threading.Thread(target=run_agent_turn, args=(req_id, sid, txt), daemon=True)
            t.start()
        elif req_id is not None:
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {}})


def run_account_mode():
    signed_in = [True]
    while True:
        msg = read_msg()
        if msg is None:
            break
        method = msg.get("method")
        req_id = msg.get("id")
        if method == "initialize":
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": default_init_result()})
        elif method == "_x.ai/billing":
            if not signed_in[0]:
                send_msg({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32000, "message": "Authentication required"}})
            else:
                send_msg({
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "config": {
                            "creditUsagePercent": 42.0,
                            "currentPeriod": {
                                "type": "USAGE_PERIOD_TYPE_WEEKLY",
                                "start": "2026-11-22T09:00:00Z",
                                "end": "2026-11-29T09:00:00Z",
                            },
                            "prepaidBalance": {"val": 1250},
                        },
                        "subscription_tier": "SuperGrok",
                    },
                })
        elif method == "_x.ai/auth/info":
            send_msg({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "email": "ada@example.com",
                    "firstName": "Ada",
                    "lastName": "Lovelace",
                    "teamName": "",
                    "principalType": "user",
                    "methodId": "grok.com",
                },
            })
        elif method == "_x.ai/auth/logout":
            signed_in[0] = False
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"success": True}})
        elif method == "authenticate":
            signed_in[0] = True
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"_meta": {"email": "ada@example.com"}}})
        elif method == "_x.ai/session/info":
            send_msg({
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "model": "grok-4.7",
                    "context": {"used": 35000, "total": 100000, "percent": 35.0},
                },
            })
        elif method == "session/list":
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {"sessions": []}})
        elif req_id is not None:
            send_msg({"jsonrpc": "2.0", "id": req_id, "result": {}})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", default="")
    parser.add_argument("--delay-ms", type=int, default=0)
    parser.add_argument("--mode", default="fixture")
    parser.add_argument("--marker", default="")
    args = parser.parse_args()

    if args.mode == "cancel":
        run_cancel_mode()
    elif args.mode == "crash-once":
        run_crash_once_mode(args.marker)
    elif args.mode == "concurrent":
        run_concurrent_mode()
    elif args.mode == "sessions":
        run_sessions_mode()
    elif args.mode == "agent":
        run_agent_mode()
    elif args.mode == "desk":
        run_agent_mode(listed=True)
    elif args.mode == "account":
        run_account_mode()
    elif args.fixture:
        run_fixture_mode(args.fixture, args.delay_ms)
    else:
        sys.stderr.write("fake_agent.py: specify --fixture or --mode\n")
        sys.exit(2)


if __name__ == "__main__":
    main()
