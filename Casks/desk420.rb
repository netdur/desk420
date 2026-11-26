cask "desk420" do
  version "0.1.3"
  sha256 "50e0048c41382991ac0857c99f5c8a76718bc160606ff9969c85cf477faf564a"

  url "https://github.com/netdur/desk420/releases/download/v#{version}/Desk420-#{version}-arm64.dmg"
  name "Desk420"
  desc "Native desktop client for Grok"
  homepage "https://github.com/netdur/desk420"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on arch: :arm64
  depends_on cask: "grok-build"
  depends_on macos: :ventura

  app "Desk420.app"

  zap trash: [
    "~/.desk420",
    "~/Library/Preferences/dev.cplus.Desk420.plist",
    "~/Library/Saved Application State/dev.cplus.Desk420.savedState",
  ]

  caveats <<~EOS
    Desk420.app is currently ad-hoc signed. If macOS Gatekeeper blocks the first
    launch, run:
      xattr -dr com.apple.quarantine /Applications/Desk420.app
  EOS
end
