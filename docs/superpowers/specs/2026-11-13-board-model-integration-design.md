# Board Model Integration — sdlc-orchestrator

**Data:** 2026-11-13
**Repo:** RafaTchanz/sdlc-orchestrator (versão atual 1.2.0)
**Board de referência:** dafiti-group #7 (Relic Team); modelo documentado em `dafiti-group` #56.

## 1. Intenção e por que agora

O `sdlc-github-issue` cria histórias no board sem preencher `Nível`, `Origem`, nem hierarquia de sub-issues. As histórias aparecem soltas, fora das visões Downstream e Épicos, sem o épico-pai que as agrupa. O time passou a usar um modelo de board com três níveis (Iniciativa → Épico → História), campos de datas planejadas/reais e visões separadas por nível. Este documento especifica as mudanças para que o orquestrador crie tarefas já inseridas nessa hierarquia.

## 2. Objetivos, não-objetivos, anti-objetivos

**Objetivos**

- Histórias criadas pelo `/sdlc` e `/sdlc-write-task` chegam ao board com `Nível = História`, `Origem = Upstream` e linkadas como sub-issue do épico-pai.
- O intake aceita iniciativa e épico por número, URL ou título parcial; busca no board se não for fornecido; pergunta uma vez se não encontrar.
- Um roadmap opcional (lista de épicos com datas) preenche datas planejadas dos épicos e linka épico → iniciativa antes de criar as histórias.
- Tudo best-effort: falha em qualquer step do board não trava o pipeline — issue é criada e aviso é exibido.

**Não-objetivos**

- Não altera o roll-up automático (`rollup.py`) — ele continua como rotina separada.
- Não cria a iniciativa automaticamente — ela deve existir no purchase-projects antes do intake.
- Não muda os campos `Epic` (texto) e `Projeto` (single select) já preenchidos hoje — continua preenchendo os dois além dos novos.
- Não muda o fluxo de implementação (Coder/QA/Review/Stress/Verdict).

**Anti-objetivos**

- Questões adicionais no intake que atrasem o início do pipeline sem valor claro.
- Falha no board bloquear a criação de issues ou a implementação.

## 3. Mudanças por arquivo

### 3.1 `skills/sdlc/SKILL.md` — intake ampliado

A pergunta de opt-in de GitHub Issue hoje coleta: `repos`, `board (owner + número)`, `tribo`, `squad`, `project_name`. Adicionar ao mesmo bloco de perguntas:

- **`iniciativa`** (opcional): número de issue, URL ou título parcial da iniciativa no purchase-projects (ex: `purchase-projects#26` ou `Giftback`).
- **`épico`** (opcional): idem para o épico-pai das histórias desta sessão.
- **`roadmap`** (opcional): lista de épicos com estimativas de duração e datas de início. Aceita formato livre — o `sdlc-board-planner` faz o parsing. Se não for dado, o planner não é despachado.

Regra: se `iniciativa` ou `épico` não for informado, o orquestrador tenta resolver no passo 1a antes de entrar no loop de stories (ver 3.2). Nunca bloqueia o intake por falta dessas informações.

### 3.2 `skills/sdlc/references/phases.md` — novo Step 1a e Step 5a estendido

**Novo Step 1a — Board Planner (opcional, apenas se `roadmap` foi dado no intake)**

Despachado uma única vez, antes do Step 2 (Analyst), quando o usuário forneceu um `roadmap`:

```
Agent(subagent_type: "sdlc-board-planner", prompt:
  "Board: {board owner}/{board number}.
   Iniciativa: {iniciativa, se fornecida}.
   Épico: {épico, se fornecido}.
   Roadmap: {roadmap fornecido no intake}.
   Projeto: {project_name, se fornecido}.
   Preenche épicos e linka hierarquia per your contract.")
```

O planner retorna o node ID e número de issue do épico resolvido/criado. O orquestrador guarda esse valor como `epic_issue_id` na sessão — repassado para `sdlc-github-issue` em 5a.

Se `roadmap` não foi fornecido mas `épico` foi: o orquestrador resolve o épico diretamente via `gh api graphql` (busca por número, URL ou título no board) e guarda `epic_issue_id`. Se não encontrar, pergunta uma vez. Se ainda falhar, registra `epic_issue_id = nil` — o pipeline continua, `sdlc-github-issue` cria as histórias sem sub-issue link e emite aviso.

**Step 5a estendido — dispatch de `sdlc-github-issue`**

O prompt existente passa a incluir os novos campos quando disponíveis:

```
Agent(subagent_type: "sdlc-github-issue", prompt:
  "Story files: {lista de arquivos aprovados}.
   Epic number: {n}.
   Target repo: {repo}.
   Board: {board owner}/{board number}.
   Tribo: {tribo}. Squad: {squad}.
   Project: {project_name, se fornecido}.
   Parent epic issue: {epic_issue_id, se resolvido — número de issue no purchase-projects, ex: 29}.
   Origem: Upstream.
   Create issues per your contract.")
```

`Parent epic issue` e `Origem` são omitidos do prompt quando não disponíveis — `sdlc-github-issue` trata sua ausência como "não aplicar" (ver 3.4).

### 3.3 `skills/sdlc-write-task/SKILL.md` — modo standalone

Step 4 (confirmação de criação de issue) passa a perguntar também por `iniciativa`, `épico` e `project_name` se ainda não dados.

**Resolução do épico em standalone (decisão do construtor — #1):** o step 4 roda inline a mesma resolução da tabela da seção 4: busca `gh api graphql` por número/URL ou por título parcial com filtro `Nível = Épico` + `Projeto = project_name`, podendo fazer uma pergunta de follow-up ao usuário se ambíguo. O resultado é o `epic_issue_id` (número de issue). Título parcial é suportado igual ao `/sdlc`; não há modo simplificado que aceite só número.

**Link épico → iniciativa em standalone (decisão do construtor — #1):** se `iniciativa` foi coletada e `epic_issue_id` foi resolvido, o step 4 cria o link épico→iniciativa inline (`addSubIssue`) antes de despachar `sdlc-github-issue`. Se apenas um dos dois estiver disponível, o link é pulado (sem aviso de erro, já que é opcional). `sdlc-github-issue` não faz esse link — ele só linka histórias ao épico.

O dispatch de `sdlc-github-issue` em step 5 segue o mesmo padrão estendido de 3.2.

### 3.4 `agents/sdlc-github-issue.md` — Falcão estendido

Após o step existente 3.vii (setagem de `Epic` e `Projeto`), adicionar **step 3.viii-a** (antes de append da URL no step 3.viii):

**3.viii-a — Board model fields (best-effort, apenas quando `Origem` chegou no prompt)**

A presença de `Origem` no prompt é o flag que indica que este board usa o modelo de três níveis. Sem ele, nenhum dos steps abaixo é executado — compatibilidade retroativa total.

a. **`Nível = História`**: resolver o field ID de `Nível` via `gh project field-list` (reusa o já feito no step 3.vi — não re-fetchar). Setar via `gh api graphql updateProjectV2ItemFieldValue` com `singleSelectOptionId` da opção `História`. Falha → warning, continua.

b. **`Origem`**: setar o valor recebido no prompt (`Upstream`). Mesmo mecanismo. Falha → warning, continua.

c. **Sub-issue link (épico-pai)**: se `Parent epic issue` estiver no prompt, resolver o node ID da issue-pai via `gh api graphql` (`repository(owner:"dafiti-group", name:"purchase-projects").issue(number: N).id`). Chamar `addSubIssue(issueId: <pai>, subIssueId: <filho>)` com header `GraphQL-Features: sub_issues`. Se a resposta indicar que a sub-issue já existe, ignorar silenciosamente. Qualquer outra falha → warning não-fatal, continua.

**Regra de idempotência existente**: se a issue já existia (step 3.i detectou `**GitHub Issue**:` no arquivo), nenhum dos steps viii-a é executado.

**Handoff atualizado**: acrescentar ao texto de saída o número de sub-issue links criados e campos setados, ex: `"3/3 issues criadas, 3/3 linkadas ao épico #29, 6/6 campos board-model setados."`.

### 3.5 Novo `agents/sdlc-board-planner.md`

**Frontmatter (decisão do construtor — #3):** `model: sonnet, tools: Read, Bash`. `Read` é necessário para referenciar a função `add_workdays` de `~/docs/board-sdlc/board7/giftback.py` (ver seção 6). `Write` não é necessário — o agente nunca escreve arquivos. `Bash` para todas as chamadas `gh`.

**Contrato**

- **Input**: board (owner + número), iniciativa (número/URL/título ou nil), épico (número/URL/título ou nil), roadmap (texto livre com épicos + estimativas + data de início), project_name (opcional).
- **Output**: épico resolvido/criado no purchase-projects (number + node ID), linkado à iniciativa se ambos existirem. Datas planejadas preenchidas se roadmap fornecido. Handoff de uma linha com `epic_issue_id`.
- **Boundary**: best-effort. Falha em qualquer step é aviso não-fatal. Nunca toca em campos que já têm valor. Nunca cria a iniciativa.

**Procedimento**

1. Resolver a iniciativa: buscar pelo número, URL ou título parcial no board via `gh api graphql` (`ProjectV2.items` com filtro `nível:Iniciativa`). Se não encontrar → `iniciativa_id = nil`, warning, continua.

2. Resolver o épico:
   - Se número/URL fornecido: buscar diretamente.
   - Se título parcial: buscar issues com `Nível = Épico` e `Projeto = project_name` no board, primeiro match.
   - Se não encontrado e roadmap fornecido: criar a issue no purchase-projects (título = nome do épico do roadmap, label `piloto-board`), adicionar ao board, setar `Nível = Épico`, `Origem = Upstream`, `Projeto = project_name`.
   - Se não encontrado e sem roadmap: `épico_id = nil`, warning, continua.

3. Ligar épico → iniciativa: se ambos resolvidos, chamar `addSubIssue`. Idempotente — "already exists" é ignorado silenciosamente.

4. Preencher datas planejadas do épico: parsear o roadmap, calcular datas em dias úteis a partir da data de início (igual ao `board7/giftback.py` existente em `~/docs/board-sdlc/`). Setar `Início dev (plan.)`, `Fim dev (plan.)`, `Entrega prod (plan.)` somente se vazios. Falha por campo → warning por campo.

5. Handoff: `"Board planner: épico #{n} ({título}) resolvido, linkado à iniciativa #{m}, {k}/3 datas preenchidas."` — ou `"Board planner: épico não resolvido — histórias serão criadas sem sub-issue link."` se épico_id = nil.

## 4. Comportamento de descoberta do épico (sem roadmap)

| O que o usuário forneceu                              | O que o orquestrador faz                                                                                                      |
| ----------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Número/URL exato (ex: `29` ou `purchase-projects#29`) | Resolve diretamente via `gh api graphql`                                                                                      |
| Título parcial (ex: `"Calculate promotion"`)          | Busca no board `Nível = Épico` + `Projeto = project_name`, primeiro match; se ambíguo, lista os 3 primeiros e pergunta        |
| Nada, mas `project_name` existe                       | Busca `Nível = Épico` + `Projeto = project_name`; se único → usa; se múltiplos → lista até 3 e pergunta; se nenhum → pergunta |
| Nada e sem `project_name`                             | Pergunta diretamente: qual o número ou título do épico?                                                                       |

## 5. Restrições técnicas

- Busca por épico usa `gh api graphql` com `ProjectV2.items` + filtro. **O `gh.py` do rollup (`~/docs/board-sdlc/gh.py`) não é uma dependência** — ele está fora do repo sdlc-orchestrator e não pode ser importado por um agente que não conhece o filesystem do usuário. O builder deve inlinar a query GraphQL equivalente no `sdlc-board-planner.md` (decisão do construtor — #2). O padrão de query a seguir: `organization(login:"dafiti-group") { projectV2(number: N) { items(first:100, query:"nível:Épico projeto:{project_name}") { nodes { content { ... on Issue { id number title } } } } } }`.
- `addSubIssue` requer o header `GraphQL-Features: sub_issues`.
- `updateProjectV2ItemFieldValue` para Nível/Origem usa `singleSelectOptionId` — IDs resolvidos em runtime via `gh project field-list`, nunca hardcoded.
- Conta `gh` ativa deve ser `RafaSLorente` para o board dafiti-group.
- Compatibilidade retroativa: a ausência de `Origem` no prompt de `sdlc-github-issue` desativa todos os novos steps — boards sem o modelo continuam funcionando sem alteração.

## 6. O que fica para o construtor

- Parsing exato do campo `roadmap` no intake (texto livre vs. tabela markdown vs. lista).
- Texto dos handoffs e warnings em português.
- Ordem exata dos novos campos na pergunta de intake — caber na pergunta existente de GitHub Issue, não criar pergunta separada.
- Estratégia de desambiguação quando múltiplos épicos batem no título parcial (listar os 3 primeiros com número e título).
- Código de cálculo de dias úteis para o `sdlc-board-planner` — pode reutilizar a função `add_workdays` de `~/docs/board-sdlc/board7/giftback.py`.

## 7. Fora do escopo desta PR (próximos passos)

- Criar a iniciativa automaticamente se não existir.
- Preencher datas do épico a partir de estimativas no epic-manifest (sem roadmap explícito).
- Suporte a épicos em repos além de purchase-projects.
- Migrar cron para GitHub Actions no purchase-projects.

## 8. Decisões de implementação (2026-11-16)

Tomadas na implementação; cada uma substitui o trecho correspondente acima.

- **O planner é despachado sempre que houver opt-in de GitHub Issue, com ou sem roadmap** (substitui 3.2 "apenas se `roadmap`" e a resolução inline de 3.3). Toda consulta e escrita de hierarquia acima da história fica num só lugar (`sdlc-board-planner`), em vez de repetida em `/sdlc` e `/sdlc-write-task`. Sem roadmap ele só resolve e linka; com roadmap também cria épicos e planeja datas. Como subagente não pode perguntar ao usuário, ele devolve `AMBÍGUA`/`NÃO ENCONTRADA` e a skill pergunta uma vez e redespacha.
- **Modelo detectado pelo board, não perguntado**: o planner verifica se o board tem o campo `Nível`; se não, devolve `MODELO AUSENTE` e todos os dispatches seguem como na 1.2.0.
- **Vários épicos por sessão**: o roadmap pode trazer vários épicos, então a sessão guarda um `epic_map`. Cada epic do `epic-manifest` é mapeado ao seu épico do board no GATE 4, junto com a aprovação do lote; o arquiteto recebe os nomes dos épicos planejados para alinhar os epics.
- **`Parent epic` como `owner/repo#N`** em vez de número com `purchase-projects` fixo — o repositório da tribo é um dado da sessão, nunca hardcoded.
- **`Status` das histórias = `Ready to dev`** (aprovadas no GATE 4 ou escritas pelo `/sdlc-write-task` com DoR/AC). Sem isso o workflow nativo "Item added" deixaria a história em Backlog, fora da visão Downstream.
- **Épico criado pelo planner nasce em `Ready to Refin`**, sem a label `piloto-board` (era só do piloto). Datas planejadas da iniciativa também são preenchidas (só se vazias).
- **Datas calculadas com `python3`**, nunca de cabeça; o planner não depende de `~/docs/board-sdlc/`.
- **Correção no Falcão**: ao criar uma opção nova de `Projeto`, as opções existentes são reenviadas com `id` — sem ele, o GitHub recria as opções e todos os cards perdem o valor.
- **Trava contra duplicata (após teste e revisão)**: um épico do roadmap só é criado quando a iniciativa foi resolvida, o repositório da tribo é conhecido, nenhuma busca falhou, e todos os épicos já existentes sob a iniciativa foram reconhecidos por outra entrada — ou o humano confirmou que é novo (`Criar épicos`). O reconhecimento usa primeiro o rótulo (`E2`) e depois o nome, só entre os sub-issues com `Nível = Épico`.
- **Issue sem `Nível` não é reclassificada sozinha**: um número informado que não tem `Nível` no board volta como `NÃO CLASSIFICADO` e só é usado depois que o humano confirma (`Confirmados`).
- **Repositório da tribo opcional**: nunca é perguntado antes do despacho; sem ele, vale o repositório da iniciativa resolvida.
- **Perguntas ao humano**: no máximo 3 despachos do planner na Step 1a, nunca a mesma pergunta duas vezes. A escolha de épico de cada epic no GATE 4 fica guardada (`epic-{n}`) e não é perguntada de novo nos lotes seguintes.
- **Status confirmado depois da automação do board**: como o workflow nativo "Item added" pode sobrescrever o Status logo após a inclusão, os agentes releem o Status 5 s depois e reaplicam uma vez.
