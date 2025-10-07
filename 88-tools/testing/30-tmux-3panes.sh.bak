#!/bin/bash

SESSION="CTRL+B, D = exit"

# ─── Kill any existing session ─────────────────────────────────────────────────
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "🔁 Killing existing tmux session: $SESSION"
  tmux kill-session -t "$SESSION"
fi

# ─── Build pane commands with fallback if ccze is missing ─────────────────────
LOG_CMD() {
  echo "docker logs -f $1 2>&1 | ccze -A || docker logs -f $1"
}

# ─── Create a fresh tmux session with three stacked panes ──────────────────────
tmux new-session -d -s "$SESSION" -n logs

# Pane 0: ingest-service
tmux send-keys -t "$SESSION:0.0" "$(LOG_CMD ingest-service)" C-m

# Split vertically for device-manager
tmux split-window -v -t "$SESSION:0.0"
tmux send-keys -t "$SESSION:0.1" "$(LOG_CMD device-manager)" C-m

# Split vertically again for analytics-service
tmux split-window -v -t "$SESSION:0.1"
tmux send-keys -t "$SESSION:0.2" "$(LOG_CMD analytics-service)" C-m

# Balance layout evenly
tmux select-layout -t "$SESSION" even-vertical

# ─── If already inside tmux, just switch-client; else attach ──────────────────
if [ -n "$TMUX" ]; then
  echo "🪄 Switching to new tmux session inside current tmux..."
  tmux switch-client -t "$SESSION"
else
  echo "🧿 Attaching to tmux session: $SESSION"
  tmux attach-session -t "$SESSION"
fi