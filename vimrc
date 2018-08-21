


set ignorecase
set smartcase
set hlsearch
set number
set nowrap
set smartindent

"show invisible char
set listchars=tab:>-,trail:-
set list
hi SpecialKey ctermfg=red  guifg=yellow

"tab is substituted by 4 space
set tabstop=4
set expandtab
retab


bind -x '"\C-l": echo -e "\n\n\n\n\n\n\n\n"; clear; ls' 》》》绑定快捷键到命令；这样按了ctrl+l后清屏而且可以和以往的输出分割开



