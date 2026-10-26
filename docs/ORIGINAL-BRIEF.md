# PROMPT — Criar um tema completo para Omarchy

> Prompt reescrito (2026-10-19) a partir do primeiro prompt do projeto Lula,
> com tudo que foi aprendido ao construir, auditar e publicar o tema dark.
> Padrões verificados no sistema em: RESEARCH.md (fonte da verdade,
> incluindo §11 pós-4.0.5). Última versão testada do Omarchy: **4.0.5-1**.

---

**PROMPT:**

Crie, teste e publique um tema completo para Omarchy. Trabalhe somente na
pasta do projeto atual (ela é a raiz do repositório git do tema). Antes de
escrever qualquer arquivo, pesquise e grave os achados em RESEARCH.md;
scripts instalados vencem qualquer documentação da internet.

## 0. Pesquisa antes de implementar

- Registre em `RESEARCH.md` (inglês, com fontes) — e mantenha após updates:
  `omarchy theme refresh` re-gera os configs; re-auditar quando o Omarchy
  atualizar.
- Fontes: `/usr/share/omarchy/bin/*` (scripts são autoritativos),
  `/usr/share/omarchy/default/themed/*.tpl` (templates built-in),
  `/usr/share/omarchy/themes/*` (temas oficiais como referência de estrutura,
  inclusive os light: catppuccin-latte, flexoki-light) e
  omarchy.org/manual + omarchythemes.dev (convenções).
- Confirmar no sistema: fluxo `omarchy theme install`/`set`/`refresh`,
  staging em `~/.local/state/omarchy/current/theme/`, deny list de temas git,
  resolução de placeholders e o contrato Plymouth/Opcional OWE.

## 1. Nome e repositório

- Repositório: `omarchy-<nome>-theme` (minúsculas, `[a-z0-9._-]`).
  O slug instalado sai da URL ao remover `omarchy-…`/`…-theme`
  (ex.: `omarchy-lula-light-theme` → tema `lula-light`).
- Um tema por repositório; variantes (dark/light) são temas-irmãos em
  repositórios separados, com nomes `Lula` / `Lula Light`.
- Conta/repo no GitHub; branch `main`; tags de versão (`v1.0`…) com release
  notes.

## 2. Arquivos do tema (contrato verificado)

Obrigatórios:

- `colors.toml` — a única fonte real do tema:
  - `mode = "dark"` ou `"light"` (chave resolve sozinha; não usar arquivos
    `light.mode`).
  - 26 chaves canônicas explícitas: accent, selection, muted, background,
    dark_background, darker_background, lighter_background, foreground,
    dark_foreground, light_foreground, bright_foreground, red, yellow,
    orange, green, cyan, blue, magenta, brown e os bright_red/yellow/
    green/cyan/blue/magenta.
  - Em temas light: `foreground` é o texto ESCURO, `bright_foreground`
    igual a `foreground`, `light_foreground` um pouco menos contrastado,
    `dark_foreground` só para cromo, superfícies recuam para tons mais
    escuros (dark/darker_background), e ANSI precisa permanecer legível
    sobre papel (oficiais usam bright == valor base nos tons fracos).
- `backgrounds/` — flat (1 nível), ≥2560×1440, cada arquivo <3 MB,
  jpg/jpeg/png/gif/bmp/webp; JPEG para fotografia/gradiente, PNG para
  gráfico plano; NÃO incluir subpastas (`backgrounds/intros/` só teria
  sentido para o OWE — omitir por padrão).
- `preview.png` — 1800×1012, **screenshot real** do desktop com o tema
  aplicado (workspace limpo + console `omarchy dev theme-preview <tema>
  --no-osc`; workflow: ws 99 → foot → `grim` → resize → fechar janela →
  voltar ao ws do usuário).
- `unlock.png` — arte transparente (logo/cadeado) legível na tela de lock;
  `preview-unlock.png` — 1920×1080 gerado com
  `omarchy plymouth preview "<bg hex>" "<fg hex>" unlock.png
  preview-unlock.png` (roda com `timeout 5`: o final sempre "pendura" no
  `imv`, que é o visualizador — não é bug, feche a janela; o PNG é escrito
  antes).

Opcionais:

- `icons.theme` — `Yaru-<variante>` (ex.: `Yaru-red`).
- `keyboard.rgb` — 6 hex sem `#` (ex.: `e63950`).

PROIBIDOS (deny list de `omarchy-theme-set` — ignorados em temas git): `*.lua`
qualquer, `alacritty.toml`, `foot.ini`, `ghostty.conf`, `kitty.conf`,
`vscode.json` e **symlinks**. Tudo isso regenera dos templates built-in a
partir de `colors.toml` — não enviar. README/RESEARCH/LICENSE são copiados e
não geram aviso (docs).

- Direitos dos assets: imagens próprias/IA própria OK; imagem de terceiros
  (ex.: fanart) não redistribuir sem direito — README não deve afirmar
  "no third-party images" se não for verdade.

## 3. Engenharia da paleta

- Metas de contraste: fg/bg 7:1 (piso 4,5:1); texto secundário ≥4,5:1;
  accent/bg ≥3:1 (em light use accent ~15–20% mais escuro que o dark-irmão);
  ANSI/bg ≥4,5:1 tanto quanto oficialmente possível; pares selection ≥4,5:1.
- Uma cor de destaque: `accent == red` (padrão do projeto Lula).
- NÃO redefinir chaves derivadas: `bg/fg` e `color0–15` saem da resolução
  (`omarchy-theme-color --all` resolve 71 chaves; `purple` aliasia
  `magenta`; `mode`/`theme_type` derivados). Valide com
  `omarchy-theme-color --file colors.toml --all` e depois confira que
  nenhum `{{ }}` ficou sem expandir no staging.
- Gradientes de borda (cada tema entrega):
  `hyprland_active_border = "rgba(<AAA>ee) rgba(<BBB>ee) 45deg"` e
  `hyprland_inactive_border = "rgba(<CCC>aa)"` — consumidos via
  `{{ hypr_gradient hyprland_active_border accent }}` e
  `{{ shell_gradient … }}` (em `shell.toml`).

## 4. Testes (fazer TODOS, sem inventar compatibilidade)

1. `omarchy theme install https://github.com/…/omarchy-<nome>-theme` e2e:
   clone limpo, **zero** avisos "Ignored in …", aplicação imediata.
2. `omarchy theme refresh`: repetível e idempotente em staging
   (`~/.local/state/omarchy/current/theme/` byte-a-byte entre rodadas).
3. `omarchy-theme-color --all` → 0 placeholders irrisoluvidos
   (grep por `{{` no staging fora de `.md`).
4. Ciclo de fundos: `omarchy theme bg next` gira todos os wallpapers
   (transição crossfade em 4.0.5+); `omarchy theme bg cache` gera
   thumbnails do switcher.
5. `omarchy theme current` exibe o nome; `omarchy theme list` contém o tema;
   `omarchy dev theme-preview <tema>` renderiza a paleta.
6. Você JÁ PODE romper a sessão do usuário durante testes, porque sempre:
   - salvar antes: tema ativo + background atual
     (`~/.local/state/omarchy/current/…`, `omarchy theme bg current`);
   - restaurar ao final; pedir aprovação antes de passos destrutivos
     (sudo, remoção, re-clonar).
7. Novo lugar no sistema: Plymouth é opcional e máquina-local
   (`omarchy-plymouth-set-by-theme <slug>`, sudo, revertível); não mexer
   a não ser a pedido.

## 5. Publicação

- Push em `main`, tag `vX.Y` + release notes (o que mudou, versão do
  Omarchy testada).
- README (inglês): instalação, ativação, atualização/remoção, extras
  opcionais (Plymouth/OWE), wallpapers com galeria (table com imagens) e
  compatibilidade (versões testadas).
- PR para a galeria oficial (`omacom-io/omarchy-site`, branch `master`):
  entrada `<figure>` em `themes/index.html` (ordem alfabética), asset
  `assets/themes/<slug>.webp` 1200×675 (~40–100 KB, derivado do
  `preview.png`), e `src/data/themes.json` regenerado com `npm run port`
  (o JSON vem do HTML — nunca editar só o JSON). Um mantenedor precisa
  aprovar o workflow na primeira contribuição (normal).
- Intros wallpapers animados só com OWE instalado (`omarchy pkg add owe`);
  por padrão o tema é estático.

## 6. Comunicação com o usuário

- Respostas em português; artefatos (código/docs/repo) em inglês.
- Nunca tragen disponibilidade por compatibilidade não testada.
- Ao final, listar: o que mudou no SO, o que foi publicado, pendências
  opcionais (galeria, Plymouth, OWE) e como reverter cada uma.
