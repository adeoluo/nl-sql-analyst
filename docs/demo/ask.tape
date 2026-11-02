# Records docs/demo/ask.gif from a real run: `vhs docs/demo/ask.tape` from the repo root.
Output docs/demo/ask.gif
Set Shell "bash"
Set FontSize 15
Set Width 1300
Set Height 440
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 22ms

Hide
Type `export PS1='$ ' && uv sync -q && source .venv/bin/activate && clear` Enter
Sleep 10s
Show
Type `python -m nl_sql_analyst ask "How many employees are there?"` Enter
Sleep 2s
Type `python -m nl_sql_analyst ask "What is the average salary in Engineering?"` Enter
Sleep 2.5s
