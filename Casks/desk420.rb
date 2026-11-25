cask "desk420" do
  version "0.1.0"
  sha256 "96831f4696d54197c7c8d757850a2be4e058cc1e7601cb12ac2881f6beeecd07"

  url "https://github.com/netdur/desk420/releases/download/v#{version}/Desk420-#{version}-arm64.dmg"
  name "Desk420"
  desc "Native desktop client for Grok"
  homepage "https://github.com/netdur/desk420"

  livecheck do
    url :url
    strategy :github_latest
  end

  depends_on arch: :arm64
  depends_on macos: :ventura

  app "Desk420.app"

  zap trash: [
    "~/.desk420",
    "~/Library/Preferences/dev.cplus.Desk420.plist",
    "~/Library/Saved Application State/dev.cplus.Desk420.savedState",
  ]

  caveats <<~EOS
    Desk420 drives the Grok CLI (`grok`) over ACP. Install it from Desk420's
    onboarding screen or from https://x.ai if it is not already installed.

    Desk420.app is currently ad-hoc signed. If macOS Gatekeeper blocks the first
    launch, run:
      xattr -dr com.apple.quarantine /Applications/Desk420.app
  EOS
end
