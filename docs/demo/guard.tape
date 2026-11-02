# Records docs/demo/guard.gif from a real run: `vhs docs/demo/guard.tape` from the repo root.
Output docs/demo/guard.gif
Set Shell "bash"
Set FontSize 15
Set Width 1300
Set Height 400
Set Padding 18
Set Theme "Catppuccin Mocha"
Set TypingSpeed 22ms

Hide
Type `export PS1='$ ' && uv sync -q && source .venv/bin/activate && clear` Enter
Sleep 10s
Show
Type `python -m nl_sql_analyst check "SELECT name FROM employees"` Enter
Sleep 2s
Type `python -m nl_sql_analyst check "DROP TABLE employees"` Enter
Sleep 2.5s
