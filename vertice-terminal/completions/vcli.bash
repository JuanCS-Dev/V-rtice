# Bash completion for vcli
# Generated for VÉRTICE Platform CLI (Typer 0.12+)
#
# NOTE: For best results, use Typer's native completion:
#   vcli --install-completion
#
# Alternative installation:
#   source /path/to/vertice-terminal/completions/vcli.bash
# or
#   cp completions/vcli.bash ~/.bash_completion.d/vcli

_vcli_completion() {
    local IFS=$'\n'
    local completions

    # Typer 0.12+ uses _TYPER_COMPLETE_ARGS for completion
    # This is a simplified implementation - for full features use: vcli --install-completion
    completions=$(env _TYPER_COMPLETE_ARGS="${COMP_WORDS[*]:0:$COMP_CWORD+1}" \
                      _VCLI_COMPLETE=complete_bash vcli 2>/dev/null)

    if [ -z "$completions" ]; then
        # Fallback: show basic command list
        if [ "$COMP_CWORD" -eq 1 ]; then
            COMPREPLY=($(compgen -W "adr analytics ask auth cognitive compliance context detect distributed dlp hcl hunt immunis incident investigate ip malware maximus memory menu monitor offensive osint plugin policy project scan script shell siem threat threat_intel tui" -- "${COMP_WORDS[1]}"))
        fi
    else
        COMPREPLY=($(compgen -W "$completions" -- "${COMP_WORDS[$COMP_CWORD]}"))
    fi
}

_vcli_completion_setup() {
    complete -o default -F _vcli_completion vcli
}

_vcli_completion_setup
