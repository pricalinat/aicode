# 🔍 Claude Code Viewer

Claude Code Viewer is a desktop application for viewing and analyzing Claude Code CLI session logs. It provides a graphical interface for session transcripts, rendering conversations with markdown, syntax-highlighted code blocks, and formatted tool outputs.

https://github.com/user-attachments/assets/0cd43984-9a2c-4cf7-b3f2-2abc2ebc6d2c

## 💡 Why Claude Code Viewer?

Working with Claude in the terminal is powerful, but long sessions can become hard to navigate. Claude Code Viewer bridges this gap by providing a visual interface that makes your sessions readable and manageable.

**The bidirectional workflow:**
- **Terminal → Viewer**: Type `ccviewer` in any Claude session to instantly open it in the viewer
- **Viewer → Terminal**: Click the resume button to copy the command and continue in your terminal
- Switch back and forth as needed - code in terminal, review in viewer

This seamless integration means you get the best of both worlds: the power of terminal for active coding and the clarity of a visual interface for understanding complex conversations, reviewing long outputs, or catching up on previous work.

Think of it as your session's reading glasses - everything becomes clearer when you need to review what happened, understand complex outputs, or share your work with others.

## ✨ Features

### Project & Session Management
- **Auto-Discovery**: Automatically finds all Claude projects in `~/.claude/projects/`.
- **Smart Sorting**: Sessions are sorted by modification time and grouped by date.
- **Session Preview**: Hover over a session to preview its content (can be disabled in settings).
- **Real-Time Updates**: Sessions refresh automatically as you work with the Claude CLI.
- **Recent Sessions**: A dedicated panel provides quick access to your most recent work.
- **Session Status**: Visual indicators for active, completed, and in-progress sessions.

### Advanced Message Rendering
- **Syntax Highlighting**: Code blocks are rendered with language detection.
- **Markdown Support**: Full markdown rendering for formatted text, lists, tables, and more.
- **Custom Tool Displays**: Specific rendering for file operations, bash commands, search results, and more.
- **Smart Grouping**: Consecutive tool uses are grouped into a single, collapsible block.
- **Collapsible Content**: Long messages and tool outputs can be collapsed to save space.
- **Resume Command**: Copy session continuation commands with one click to pick up where you left off.

### Navigation & Interface
- **Multi-Tab System**: Open multiple sessions across different projects.
- **Timeline Minimap**: A visual overview of the session with click-to-jump navigation.
- **Keyboard Shortcuts**: `Cmd/Ctrl+W` (close tab), `Cmd/Ctrl+B` (toggle sidebar), `Cmd/Ctrl+,` (settings).
- **Responsive Design**: The interface adapts to different window sizes.
- **Dark/Light Themes**: Matches Claude's design system.

## 🚀 Installation

### Option 1: Homebrew (macOS - Recommended)
```bash
brew tap esc5221/tap
brew install --cask claude-code-viewer
```

### Option 2: Direct Download
Download the latest release for your operating system from the [GitHub Releases](https://github.com/esc5221/claude-viewer/releases) page.

### Option 3: Build from Source
Requires Node.js 18+.

```bash
# Clone the repository and install dependencies
git clone https://github.com/esc5221/claude-viewer.git
cd claude-code-viewer
npm install

# Build and package for your platform
npm run dist:mac    # macOS (.dmg)
npm run dist:win    # Windows (.exe)
npm run dist:linux  # Linux (.AppImage)
```

## 💻 Usage

### From the Claude CLI
While in a Claude session (`CLAUDECODE=1` is set):
```bash
# Opens the current session in the viewer
ccviewer
# or
claude-viewer
```

### As a Standalone App
1.  Launch Claude Code Viewer.
2.  Select a project from the auto-discovered list in the sidebar.
3.  Click any session to open it in a new tab.

## 🛠️ Development

```bash
# Run development server with hot reload
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build

# Run tests
npm test
```

## 🔧 Tech Stack

- **Framework**: Electron
- **UI**: React 18, Tailwind CSS v4
- **Language**: TypeScript
- **Build Tool**: Vite
- **State Management**: Zustand

## 🤝 Contributing

Contributions are welcome. Please feel free to submit a Pull Request.

## 📄 License

MIT License.