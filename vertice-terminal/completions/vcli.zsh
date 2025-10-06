#compdef vcli

# Zsh completion for vcli
# Generated for VÉRTICE Platform CLI (Typer 0.12+)
#
# Installation:
#   Add to ~/.zshrc:
#     fpath+=/path/to/vertice-terminal/completions
#     autoload -Uz compinit && compinit
# or
#   cp completions/vcli.zsh /usr/local/share/zsh/site-functions/_vcli

_vcli_completion() {
    eval $(env _TYPER_COMPLETE_ARGS="${words[1,$CURRENT]}" _VCLI_COMPLETE=complete_zsh vcli)
}

compdef _vcli_completion vcli
