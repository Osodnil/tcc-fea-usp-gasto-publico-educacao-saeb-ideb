param([string]$Saida = "exportacao\Guilherme_Menezes_Araujo_Henrique_Nogueira_Pedro_Lindoso.pptx",
      [string]$Notas = "",
      [string]$Previa = "",
      [string]$Link = "")
# Monta pelo próprio PowerPoint (automação COM) os 12 slides do vídeo de apresentação (etapa 6; roteiro em
# docs/roteiro_video.md). As falas do roteiro entram como notas do apresentador. Com -Previa <pasta>, exporta um PNG
# por slide para conferência. Com -Link <url>, põe o link do YouTube no slide 1 (versão para o Moodle; a gravação
# é feita sem ele). Feche o PowerPoint antes de rodar.
$ErrorActionPreference = "Stop"
$R = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Saida = Join-Path $R $Saida

function Cor([string]$hex) {  # PowerPoint guarda a cor como BGR
    $r = [Convert]::ToInt32($hex.Substring(0, 2), 16); $g = [Convert]::ToInt32($hex.Substring(2, 2), 16)
    $b = [Convert]::ToInt32($hex.Substring(4, 2), 16); return $r + 256 * $g + 65536 * $b
}
$NAVY = "17375E"; $NAVY2 = "23497A"; $TINTA = "1F2937"; $CINZA = "5B6B7F"; $CLARO = "EEF3F9"; $BRANCO = "FFFFFF"
$CE = "2E75B6"; $BA = "D9692A"; $GELO = "C9D7EA"
$TIT = "Cambria"; $CORPO = "Calibri"

function Texto($s, [string]$t, $l, $tp, $w, $h, $tam, [string]$cor = $TINTA, [bool]$neg = $false, [string]$fonte = $CORPO,
               [int]$alin = 1, [bool]$ital = $false) {
    $x = $s.Shapes.AddTextbox(1, $l, $tp, $w, $h)
    $x.TextFrame.WordWrap = -1; $x.TextFrame.AutoSize = 0
    $x.TextFrame.MarginLeft = 0; $x.TextFrame.MarginRight = 0; $x.TextFrame.MarginTop = 0; $x.TextFrame.MarginBottom = 0
    $tr = $x.TextFrame.TextRange; $tr.Text = $t
    $tr.Font.Name = $fonte; $tr.Font.Size = $tam; $tr.Font.Bold = [int]$neg; $tr.Font.Italic = [int]$ital
    $tr.Font.Color.RGB = (Cor $cor); $tr.ParagraphFormat.Alignment = $alin
    return $x
}
function Caixa($s, $l, $tp, $w, $h, [string]$cor, [bool]$redonda = $true) {
    $x = $s.Shapes.AddShape($(if ($redonda) { 5 } else { 1 }), $l, $tp, $w, $h)
    if ($redonda) { $x.Adjustments.Item(1) = 0.08 }
    $x.Fill.ForeColor.RGB = (Cor $cor); $x.Fill.Solid(); $x.Line.Visible = 0; $x.Shadow.Visible = 0
    return $x
}
function Fundo($s, [string]$cor) { $s.FollowMasterBackground = 0; $s.Background.Fill.Solid(); $s.Background.Fill.ForeColor.RGB = (Cor $cor) }
function Titulo($s, [string]$t) { $null = Texto $s $t 48 34 864 46 30 $NAVY $true $TIT }
function Rodape($s, [int]$n) {
    $null = Texto $s "Gasto público por aluno e desempenho no Saeb  ·  FEA/USP  ·  2026" 48 508 700 16 10 $CINZA
    $null = Texto $s "$n" 872 508 40 16 10 $CINZA $false $CORPO 3
}

function Tela($s, [string]$img, $chaves, [string]$legenda) {  # captura do painel à esquerda, dois destaques à direita
    $p = $s.Shapes.AddPicture((Join-Path $R (Join-Path "docs/resultados/telas" $img)), 0, -1, 48, 104, 600, 337.5)
    $p.Line.Visible = -1; $p.Line.ForeColor.RGB = (Cor "D1D5DB"); $p.Line.Weight = 0.75
    $null = Texto $s $legenda 48 448 600 20 13 $CINZA $false $CORPO 1 $true
    for ($i = 0; $i -lt $chaves.Count; $i++) {
        $tp = 112 + $i * 150
        $f = Caixa $s 676 $tp 40 4 $BA $false
        $null = Texto $s $chaves[$i][0] 676 ($tp + 16) 236 50 $(if ($chaves[$i][0].Length -gt 8) { 24 } else { 40 }) $NAVY $true $TIT
        $null = Texto $s $chaves[$i][1] 676 ($tp + 72) 236 60 15 $TINTA
    }
}

$notasTxt = @()
if ($Notas) { $notasTxt = Get-Content $Notas -Raw -Encoding UTF8 | ConvertFrom-Json }
else {  # sem -Notas, as falas vêm direto do roteiro (linha "> " logo depois de cada "**Fala:**")
    $rot = Get-Content (Join-Path $R "docs\roteiro_video.md") -Raw -Encoding UTF8
    $notasTxt = @([regex]::Matches($rot, '\*\*Fala:\*\*\r?\n> (.+)') | ForEach-Object { $_.Groups[1].Value.TrimEnd() })
}

$pp = New-Object -ComObject PowerPoint.Application
try {
    $pres = $pp.Presentations.Add(0)  # sem janela; por isso o gráfico do slide 4 é desenhado com formas (AddChart2 exige janela)
    $pres.PageSetup.SlideWidth = 960; $pres.PageSetup.SlideHeight = 540
    $T = "Gasto público por aluno e desempenho no Saeb: uma análise das redes públicas brasileiras com apoio de Business Intelligence"

    # 1 · abertura: bloco centrado na altura do slide (a gravação é feita antes de existir o link do YouTube)
    $s = $pres.Slides.Add(1, 12); Fundo $s $NAVY
    $null = Texto $s "TRABALHO DE CONCLUSÃO DE CURSO  ·  ADMINISTRAÇÃO" 48 108 864 18 12 $GELO $true
    $null = Texto $s $T 48 140 820 140 34 $BRANCO $true $TIT
    $f = Caixa $s 48 300 72 4 $BA $false
    $null = Texto $s "Guilherme Menezes Araújo  ·  Henrique Nogueira Pedro Lindoso" 48 322 864 26 20 $BRANCO
    $null = Texto $s "Orientadora: Profa. Adriana Backx Noronha Viana  ·  São Paulo, 2026" 48 356 864 22 15 $GELO
    if ($Link) {  # versão para o Moodle: o Manual pede o link do YouTube no 1º slide
        $null = Texto $s "▶  Vídeo: $Link" 48 410 864 22 15 $BRANCO $true
    }
    $null = Texto $s "Faculdade de Economia, Administração, Contabilidade e Atuária  ·  Universidade de São Paulo" 48 488 864 18 12 $GELO

    # 2 · problema e pergunta
    $s = $pres.Slides.Add(2, 12); Fundo $s $BRANCO; Titulo $s "O que queremos saber"
    $c = Caixa $s 48 110 380 330 $CLARO
    $null = Texto $s "R$ 339 bi" 76 150 330 70 54 $NAVY $true $TIT
    $null = Texto $s "receita estimada do Fundeb em 2025" 76 226 330 22 16 $TINTA
    $f = Caixa $s 76 292 56 4 $BA $false
    $null = Texto $s "Gasto e aprendizagem em sistemas separados" 76 312 320 70 22 $NAVY $true $TIT
    $c = Caixa $s 460 110 452 330 $NAVY
    $null = Texto $s "PERGUNTA DE PESQUISA" 488 140 400 18 12 $GELO $true
    $null = Texto $s "O gasto público por aluno se associa ao desempenho das redes públicas no Saeb?" 488 172 400 90 22 $BRANCO $true $TIT
    $null = Texto $s "E, considerando o gasto e o contexto de cada rede, quais entregam mais ou menos do que o esperado?" 488 290 400 90 18 $BRANCO
    Rodape $s 2

    # 3 · como a educação é financiada: rosca dupla sobre um só todo, cada R$ 100 dos impostos da cesta
    # anel interno: 75 livres × 25 para a educação (MDE); anel externo: os 25 abertos em 5 direto, 14 profissionais e 6 outras
    # (a complementação da União soma-se ao fundo e fica fora da rosca, como nota)
    $s = $pres.Slides.Add(3, 12); Fundo $s $BRANCO; Titulo $s "Como a educação é financiada"
    $cxR = 232; $cyR = 300; $LARANJA2 = "F4B183"; $CINZA2 = "E5EBF3"
    function Arco($s, $cxA, $cyA, $dA, $espA, $iniA, $fimA, [string]$corA) {  # fatia de anel: ângulos em graus, 0 = topo, sentido horário
        $a = $s.Shapes.AddShape(20, $cxA - $dA / 2, $cyA - $dA / 2, $dA, $dA)
        $a.Adjustments.Item(1) = (($iniA - 90) % 360 + 360) % 360
        $a.Adjustments.Item(2) = (($fimA - 90) % 360 + 360) % 360
        $a.Adjustments.Item(3) = $espA / $dA
        $a.Fill.ForeColor.RGB = (Cor $corA); $a.Fill.Solid(); $a.Line.ForeColor.RGB = (Cor $BRANCO); $a.Line.Weight = 1.5
        $a.Shadow.Visible = 0
    }
    # anel interno (diâmetro 236): 25 educação no quadrante de cima à direita, 75 livres no resto
    Arco $s $cxR $cyR 236 50 0 90 $BA
    Arco $s $cxR $cyR 236 50 90 360 $CINZA2
    # anel externo (diâmetro 340), só sobre os 25 da educação: 5 direto, 14 profissionais, 6 outras despesas do Fundeb
    Arco $s $cxR $cyR 340 50 0 18 $LARANJA2
    Arco $s $cxR $cyR 340 50 18 68.4 $NAVY
    Arco $s $cxR $cyR 340 50 68.4 90 $CE
    $null = Texto $s "R$ 100" ($cxR - 60) ($cyR - 26) 120 32 26 $NAVY $true $TIT 2
    $null = Texto $s "dos impostos da cesta" ($cxR - 62) ($cyR + 8) 124 16 11 $CINZA $false $CORPO 2
    $null = Texto $s "ICMS, FPM, FPE, IPVA e outros" ($cxR - 62) ($cyR + 24) 124 28 9 $CINZA $false $CORPO 2 $true
    # chave do Fundeb: arco fino por fora dos R$ 14 e R$ 6, com rótulo
    $ch = $s.Shapes.AddShape(20, $cxR - 184, $cyR - 184, 368, 368)
    $ch.Adjustments.Item(1) = 18 - 90 + 1; $ch.Adjustments.Item(2) = 0 - 1; $ch.Adjustments.Item(3) = 4 / 368
    $ch.Fill.ForeColor.RGB = (Cor $NAVY); $ch.Fill.Solid(); $ch.Line.Visible = 0; $ch.Shadow.Visible = 0
    $null = Texto $s "Fundeb: R$ 20" 352 128 110 18 13 $NAVY $true
    # legenda em árvore, na ordem em que um valor deriva do outro (linhas de ligação entre os níveis)
    $null = Texto $s "DE CADA R$ 100 DA CESTA DE IMPOSTOS" 470 112 442 18 12 $NAVY $true
    $leg = @(@(0, $CINZA2, "R$ 75", "ficam livres para o estado ou o município"),
             @(0, $BA, "R$ 25", "vão para a educação (MDE):"),
             @(1, $LARANJA2, "R$ 5", "aplicados direto pelo estado ou município"),
             @(1, "grupo", "R$ 20", "vão para o Fundeb, repartido pelas matrículas:"),
             @(2, $NAVY, "R$ 14", "no mínimo (70%), pagam os profissionais"),
             @(2, $CE, "R$ 6", "vão para outras despesas da educação"))
    $passoL = 30; $topoL = 142
    function Ligar($s, $xA, $y1, $y2, [double[]]$ramos) {  # tronco vertical e um ramo horizontal até cada filho
        $v = $s.Shapes.AddLine($xA, $y1, $xA, $y2); $v.Line.ForeColor.RGB = (Cor "A9B7C9"); $v.Line.Weight = 1
        foreach ($yR in $ramos) { $h = $s.Shapes.AddLine($xA, $yR, $xA + 14, $yR); $h.Line.ForeColor.RGB = (Cor "A9B7C9"); $h.Line.Weight = 1 }
    }
    Ligar $s 477 ($topoL + 1 * $passoL + 18) ($topoL + 3 * $passoL + 10) @(($topoL + 2 * $passoL + 10), ($topoL + 3 * $passoL + 10))
    Ligar $s 501 ($topoL + 3 * $passoL + 18) ($topoL + 5 * $passoL + 10) @(($topoL + 4 * $passoL + 10), ($topoL + 5 * $passoL + 10))
    for ($i = 0; $i -lt $leg.Count; $i++) {
        $tp = $topoL + $i * $passoL; $lx = 470 + $leg[$i][0] * 24
        $q = Caixa $s $lx ($tp + 3) 14 14 $(if ($leg[$i][1] -eq "grupo") { $BRANCO } else { $leg[$i][1] }) $false
        if ($leg[$i][1] -eq "grupo") { $q.Line.Visible = -1; $q.Line.ForeColor.RGB = (Cor $NAVY); $q.Line.Weight = 1.5 }
        $tx = $lx + 22
        $null = Texto $s $leg[$i][2] $tx $tp 60 20 15 $NAVY $true $TIT
        $null = Texto $s $leg[$i][3] ($tx + 56) ($tp + 1) (912 - $tx - 56) 20 13 $TINTA
    }
    $c = Caixa $s 470 330 442 44 $CLARO
    $null = Texto $s "+23%" 486 340 70 26 18 $BA $true $TIT
    $null = Texto $s "a União acrescenta, no mínimo, 23% ao Fundeb (VAAF, VAAT e VAAR)" 552 344 350 20 12 $TINTA
    $c = Caixa $s 470 386 442 96 $NAVY
    $null = Texto $s "COTA DO ICMS POR RESULTADOS (EC nº 108/2020)" 486 398 420 16 11 $GELO $true
    $null = Texto $s "No mínimo 10 pontos da cota dos municípios por resultados educacionais" 486 416 414 40 15 $BRANCO $true $TIT
    $null = Texto $s "No Ceará, desde 2007: 18% da cota" 486 460 414 14 12 $GELO
    Rodape $s 3

    # 4 · o que a literatura diz
    $s = $pres.Slides.Add(4, 12); Fundo $s $BRANCO; Titulo $s "O que a literatura diz"
    $lit = @(@("Gasto sozinho explica pouco", "Hanushek (1997, 2003); Menezes-Filho e Amaral (2009)"),
             @("Efeito maior para os mais pobres", "Jackson et al. (2016)"), @("Sem o contexto, redes vulneráveis parecem piores", "Alves e Soares (2013)"))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 296
        $c = Caixa $s $l 108 272 200 $CLARO
        $null = Texto $s "$($i + 1)" ($l + 22) 124 40 30 26 $BA $true $TIT
        $null = Texto $s $lit[$i][0] ($l + 22) 164 230 70 22 $NAVY $true $TIT
        $null = Texto $s $lit[$i][1] ($l + 22) 262 230 40 14 $CINZA $false $CORPO 1 $true
    }
    $c = Caixa $s 48 330 864 110 $NAVY
    $null = Texto $s "LACUNA" 76 350 600 18 12 $GELO $true
    $null = Texto $s "São raras as ferramentas que comparam, rede a rede, gasto, desempenho e contexto" 76 378 820 50 20 $BRANCO $true $TIT
    Rodape $s 4

    # 5 · dados, método e indicador
    $s = $pres.Slides.Add(5, 12); Fundo $s $BRANCO; Titulo $s "Dados, método e indicador"
    $passos = @(@("8 bases públicas", "gasto · nota · contexto"), @("2 comparações", "entre municípios e no mesmo município"),
                @("Indicador", "nota real × esperada, com o mesmo gasto e contexto"), @("Painel em Power BI", "pares e alertas"))
    for ($i = 0; $i -lt 4; $i++) {
        $l = 48 + $i * 222
        $c = Caixa $s $l 112 196 180 $(if ($i -eq 3) { $NAVY } else { $CLARO })
        $corT = $(if ($i -eq 3) { $BRANCO } else { $NAVY }); $corS = $(if ($i -eq 3) { $GELO } else { $TINTA })
        $null = Texto $s "$($i + 1)" ($l + 20) 128 40 30 26 $(if ($i -eq 3) { $GELO } else { $BA }) $true $TIT
        $null = Texto $s $passos[$i][0] ($l + 20) 168 160 26 18 $corT $true
        $null = Texto $s $passos[$i][1] ($l + 20) 204 160 80 16 $corS
        if ($i -lt 3) { $a = $s.Shapes.AddShape(33, $l + 200, 192, 18, 22); $a.Fill.ForeColor.RGB = (Cor $GELO); $a.Line.Visible = 0 }
    }
    $null = Texto $s "SIOPE, Siconfi, Saeb, Censo Escolar, Censo Demográfico, IDHM, IPCA e malha municipal" 68 236 160 50 11 $CINZA $false $CORPO 1 $true
    # números do estudo numa faixa da largura dos blocos, cada um centrado na sua coluna
    $c = Caixa $s 48 316 864 96 $CLARO
    $fatos = @(@("2017–2025", "5 edições do Saeb"), @("~5.500", "redes municipais"), @("27", "redes estaduais"))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 288
        $null = Texto $s $fatos[$i][0] $l 332 288 34 28 $NAVY $true $TIT 2
        $null = Texto $s $fatos[$i][1] $l 372 288 22 15 $CINZA $false $CORPO 2
        if ($i -gt 0) { $d = $s.Shapes.AddLine($l, 334, $l, 394); $d.Line.ForeColor.RGB = (Cor "C9D7EA"); $d.Line.Weight = 1 }
    }
    $null = Texto $s "Scripts feitos com o auxílio de IA, em acordo com a orientadora." 48 440 864 20 13 $CINZA $false $CORPO 1 $true
    Rodape $s 5

    # 6 · resultado 1 (gráfico desenhado com formas)
    $s = $pres.Slides.Add(6, 12); Fundo $s $BRANCO; Titulo $s "O gasto, sozinho, explica pouco"
    $null = Texto $s "Correlação entre gasto por aluno e nota (Anos Iniciais, Matemática)" 48 104 500 20 14 $TINTA $true
    $rho = @(@("2017", 0.46), @("2019", 0.41), @("2021", 0.33), @("2023", 0.26), @("2025", 0.16))
    $base = 410; $alt = 240  # 0,50 = 240 pontos de altura
    $eixo = $s.Shapes.AddLine(48, $base, 540, $base); $eixo.Line.ForeColor.RGB = (Cor "D1D5DB"); $eixo.Line.Weight = 1
    for ($i = 0; $i -lt 5; $i++) {
        $h = $rho[$i][1] / 0.5 * $alt; $l = 70 + $i * 94
        $col = Caixa $s $l ($base - $h) 60 $h $(if ($i -eq 4) { $BA } else { $NAVY }) $false
        $null = Texto $s ("{0:0.00}" -f $rho[$i][1]).Replace(".", ",") ($l - 10) ($base - $h - 26) 80 22 16 $(if ($i -eq 4) { $BA } else { $NAVY }) $true $CORPO 2
        $null = Texto $s $rho[$i][0] ($l - 10) ($base + 8) 80 20 13 $CINZA $false $CORPO 2
    }
    $c = Caixa $s 580 100 332 160 $NAVY
    $null = Texto $s "+0,2 ponto" 604 120 290 50 40 $BRANCO $true $TIT
    $null = Texto $s "a cada 10% a mais de gasto por aluno, no mesmo município" 604 176 290 70 15 $GELO
    $c = Caixa $s 580 278 332 152 $CLARO
    $null = Texto $s "MAIOR EM" 604 298 290 18 12 $NAVY $true
    $null = Texto $s "municípios pequenos · Nordeste e Norte" 604 324 290 80 22 $NAVY $true $TIT
    $null = Texto $s "Associação, e não efeito causal." 48 448 500 20 13 $CINZA $false $CORPO 1 $true
    Rodape $s 6

    # 7 · resultado 2: Ceará × Bahia
    $s = $pres.Slides.Add(7, 12); Fundo $s $BRANCO; Titulo $s "Mesmo gasto, resultados diferentes"
    $lados = @(@("Ceará", $CE, "R$ 11.391", "242,4", "90%"), @("Bahia", $BA, "R$ 11.231", "200,1", "38%"))
    for ($i = 0; $i -lt 2; $i++) {
        $l = 48 + $i * 290; $v = $lados[$i]
        $c = Caixa $s $l 104 270 336 $CLARO
        $h = Caixa $s $l 104 270 50 $v[1]
        $null = Texto $s $v[0] ($l + 22) 116 230 28 22 $BRANCO $true $TIT
        $null = Texto $s $v[4] ($l + 22) 168 230 64 54 $v[1] $true $TIT
        $null = Texto $s "das redes acima do esperado" ($l + 22) 236 230 20 14 $TINTA
        $null = Texto $s "Gasto mediano por aluno" ($l + 22) 280 230 18 13 $CINZA
        $null = Texto $s $v[2] ($l + 22) 298 230 26 20 $TINTA $true
        $null = Texto $s "Nota média (AI, Matemática)" ($l + 22) 344 230 18 13 $CINZA
        $null = Texto $s "$($v[3]) pontos" ($l + 22) 362 230 26 20 $TINTA $true
    }
    $null = Texto $s "Redes municipais, 2023" 48 452 560 18 12 $CINZA $false $CORPO 1 $true
    $c = Caixa $s 646 104 266 336 $NAVY
    $null = Texto $s "O QUE ISSO SUGERE" 668 130 226 18 12 $GELO $true
    $null = Texto $s "Gestão e incentivos pesam mais que o volume de recursos" 668 166 226 150 24 $BRANCO $true $TIT
    $null = Texto $s "Cota do ICMS por resultados e assistência técnica" 668 350 226 60 14 $GELO $false $CORPO 1 $true
    Rodape $s 7

    # 8 · o painel e as três perguntas
    $s = $pres.Slides.Add(8, 12); Fundo $s $BRANCO; Titulo $s "O painel: três perguntas para o gestor"
    Tela $s "03_eficiencia.png" @() "Página Desempenho do painel (Anos Iniciais, Matemática, 2023)"
    # à direita: as três perguntas numeradas, uma por linha, e o destaque de 46% abaixo
    $null = Texto $s "TRÊS PERGUNTAS" 676 110 236 18 12 $NAVY $true
    $perg = @("Gastar mais se associa a aprender mais?", "Minha rede entrega o esperado?", "Com quem conversar?")
    for ($i = 0; $i -lt 3; $i++) {
        $tp = 138 + $i * 58
        $null = Texto $s "$($i + 1)" 676 $tp 24 30 24 $BA $true $TIT
        $null = Texto $s $perg[$i] 706 ($tp + 3) 206 46 16 $NAVY $true
    }
    $f = Caixa $s 676 322 40 4 $BA $false
    $null = Texto $s "46%" 676 338 236 50 40 $NAVY $true $TIT
    $null = Texto $s "das redes acima do esperado em 2023" 676 394 236 40 15 $TINTA
    Rodape $s 8

    # 9 · minha rede e meus pares (duas capturas lado a lado)
    $s = $pres.Slides.Add(9, 12); Fundo $s $BRANCO; Titulo $s "Minha rede entrega o esperado? Com quem conversar?"
    $duas = @(@("caso_a_ficha.png", "+24%  ·  melhor que 98% das redes", "Ficha do município: Timon (MA), 2023"),
              @("caso_a_pares.png", "161 pares  ·  só 1 entrega mais", "Página Pares: Timon (MA) e Pacajus (CE)"))
    for ($i = 0; $i -lt 2; $i++) {
        $l = 48 + $i * 444
        $p = $s.Shapes.AddPicture((Join-Path $R (Join-Path "docs/resultados/telas" $duas[$i][0])), 0, -1, $l, 108, 420, 236.25)
        $p.Line.Visible = -1; $p.Line.ForeColor.RGB = (Cor "D1D5DB"); $p.Line.Weight = 0.75
        $f = Caixa $s $l 364 40 4 $BA $false
        $null = Texto $s $duas[$i][1] $l 378 420 30 22 $NAVY $true $TIT
        $null = Texto $s $duas[$i][2] $l 418 420 20 13 $CINZA $false $CORPO 1 $true
    }
    Rodape $s 9

    # 10 · os alertas
    $s = $pres.Slides.Add(10, 12); Fundo $s $BRANCO; Titulo $s "Conferir antes de copiar"
    Tela $s "caso_c_ficha.png" @(@("+70%", "acima do esperado em 2023"), @("salto atípico", "a nota mudou demais desde a edição anterior")) "Ficha do município: Coruripe (AL), com alerta de salto atípico"
    Rodape $s 10

    # 11 · conclusões, contribuições e limitações: três cartões iguais, como os de Ceará × Bahia
    $s = $pres.Slides.Add(11, 12); Fundo $s $BRANCO; Titulo $s "Conclusões, contribuições e limitações"
    # cada item: @(rótulo opcional, texto)
    $cols = @(@("Conclusões", $NAVY, @(@("", "Gasto sozinho explica pouco"), @("", "Mesmo gasto, resultados diferentes"))),
              @("Contribuições", $CE, @(@("PRÁTICA", "O painel, com pares e alertas"), @("TEÓRICA", "Evidência de 2017 a 2025, já sob o Novo Fundeb"))),
              @("Limitações", $BA, @(@("", "Associação, não causa"), @("", "Contexto só por UF, até 2024"), @("", "Sem teste com gestores"))))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 296; $k = $cols[$i]; $itens = $k[2]
        $c = Caixa $s $l 104 272 340 $CLARO
        $h = Caixa $s $l 104 272 52 $k[1] $false
        $null = Texto $s $k[0] ($l + 22) 117 230 28 20 $BRANCO $true $TIT
        $passo = 264 / $itens.Count
        for ($j = 0; $j -lt $itens.Count; $j++) {
            $tp = 178 + $j * $passo
            if ($j -gt 0) { $d = $s.Shapes.AddLine($l + 22, $tp - 16, $l + 250, $tp - 16); $d.Line.ForeColor.RGB = (Cor "C9D7EA"); $d.Line.Weight = 1 }
            if ($itens[$j][0]) {
                $null = Texto $s $itens[$j][0] ($l + 22) $tp 230 16 11 $k[1] $true
                $tp += 20
            }
            $null = Texto $s $itens[$j][1] ($l + 22) $tp 230 70 19 $NAVY $true $TIT
        }
    }
    Rodape $s 11

    # 12 · fechamento
    $s = $pres.Slides.Add(12, 12); Fundo $s $NAVY
    $null = Texto $s "Obrigado!" 48 120 520 70 54 $BRANCO $true $TIT
    $null = Texto $s "O painel e todo o código estão abertos." 48 210 520 30 20 $GELO
    $null = Texto $s "Leia o QR Code ou acesse:" 48 262 520 24 16 $GELO
    $null = Texto $s "github.com/Osodnil/tcc-fea-usp-gasto-publico-educacao-saeb-ideb" 48 290 540 24 16 $BRANCO $true
    $q = Caixa $s 640 110 250 250 $BRANCO
    $null = $s.Shapes.AddPicture((Join-Path $R "docs\resultados\figuras\qrcode_acesso.png"), 0, -1, 655, 125, 220, 220)
    $null = Texto $s "Guilherme Menezes Araújo  ·  Henrique Nogueira Pedro Lindoso  ·  FEA/USP, 2026" 48 470 864 20 13 $GELO

    # notas do apresentador = falas do roteiro
    for ($i = 1; $i -le $pres.Slides.Count; $i++) {
        if ($notasTxt.Count -ge $i) { $pres.Slides.Item($i).NotesPage.Shapes.Placeholders.Item(2).TextFrame.TextRange.Text = $notasTxt[$i - 1] }
    }
    if (Test-Path $Saida) { Remove-Item $Saida }
    $pres.SaveAs($Saida, 24)
    "[OK] $Saida ($($pres.Slides.Count) slides)"
    if ($Previa) {
        New-Item -ItemType Directory -Force $Previa | Out-Null
        for ($i = 1; $i -le $pres.Slides.Count; $i++) { $pres.Slides.Item($i).Export((Join-Path $Previa ("slide{0}.png" -f $i)), "PNG", 1600, 900) }
    }
    $pres.Close()
} catch {
    "ERRO na linha $($_.InvocationInfo.ScriptLineNumber): $($_.InvocationInfo.Line.Trim())"; $_.Exception.Message
} finally {
    Start-Sleep 1
    try { $pp.Quit() } catch { Stop-Process -Name POWERPNT -Force -ErrorAction SilentlyContinue }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($pp) | Out-Null
}
