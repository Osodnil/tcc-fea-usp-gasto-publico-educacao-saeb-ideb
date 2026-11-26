param([string]$Saida = "exportacao\Guilherme_Menezes_Araujo_Henrique_Nogueira_Pedro_Lindoso.pptx",
      [string]$Notas = "",
      [string]$Previa = "",
      [string]$Link = "",
      [switch]$NotasFalas)
# Monta pelo próprio PowerPoint (automação COM) os 9 slides do vídeo de apresentação (etapa 6; roteiro em
# docs/roteiro_video.md). A cola de palavras-chave do roteiro entra como notas do apresentador (com -NotasFalas, as
# falas completas). Com -Previa <pasta>, exporta um PNG
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
function Rodape($s, [int]$n) {  # à esquerda, para deixar livre o canto inferior direito (vídeo do apresentador)
    $null = Texto $s "$n  ·  Gasto público por aluno e desempenho no Saeb  ·  FEA/USP  ·  2026" 48 508 600 16 10 $CINZA
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
else {  # sem -Notas, as notas vêm do roteiro: a cola de palavras-chave de cada slide (ou as falas, com -NotasFalas)
    $rot = Get-Content (Join-Path $R "docs\roteiro_video.md") -Raw -Encoding UTF8
    if ($NotasFalas) {
        $notasTxt = @([regex]::Matches($rot, '\*\*Fala:\*\*\r?\n> (.+)') | ForEach-Object { $_.Groups[1].Value.TrimEnd() })
    } else {
        $cola = $rot.Substring($rot.IndexOf("## Cola de palavras-chave"))
        $notasTxt = @([regex]::Matches($cola, '\*\*(\d+ · [^*]+)\*\*([^\r\n]*)\r?\n((?:- [^\r\n]*\r?\n?)+)') | ForEach-Object {
            $linhas = @("$($_.Groups[1].Value)$($_.Groups[2].Value)") + @($_.Groups[3].Value.Trim() -split '\r?\n' | ForEach-Object { "• " + $_.Substring(2).Trim() })
            ($linhas -join "`r") -replace '\*\*', ''
        })
    }
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

    # Em todos os slides de conteúdo, o canto inferior direito (x > 690 e y > 352) fica sem nada: é onde entra o vídeo
    # do apresentador, como sugere a Coordenação.

    # 2 · problema e pergunta
    $s = $pres.Slides.Add(2, 12); Fundo $s $BRANCO; Titulo $s "O que queremos saber"
    $c = Caixa $s 48 110 380 330 $CLARO
    $null = Texto $s "R$ 339 bi" 76 150 330 70 54 $NAVY $true $TIT
    $null = Texto $s "receita estimada do Fundeb em 2025, o fundo que financia a educação básica pública" 76 226 330 44 14 $TINTA
    $f = Caixa $s 76 292 56 4 $BA $false
    $null = Texto $s "Gasto e aprendizagem em sistemas separados" 76 312 320 70 22 $NAVY $true $TIT
    $c = Caixa $s 460 110 452 230 $NAVY
    $null = Texto $s "PERGUNTA DE PESQUISA" 488 130 400 18 12 $GELO $true
    $null = Texto $s "O gasto público por aluno se associa ao desempenho das redes públicas no Saeb?" 488 156 400 90 22 $BRANCO $true $TIT
    $null = Texto $s "E, considerando o gasto e o contexto de cada rede, quais entregam mais ou menos do que o esperado?" 488 256 400 50 16 $BRANCO
    $null = Texto $s "Saeb: avaliação nacional do Inep, com provas de Matemática e Português" 488 312 400 16 11 $GELO $false $CORPO 1 $true
    Rodape $s 2

    # 3 · como a educação é financiada: rosca dupla sobre um só todo, cada R$ 100 dos impostos da cesta
    # anel interno: 75 livres × 25 para a educação (MDE); anel externo: os 25 abertos em 5 direto, 14 profissionais e 6 outras
    # (a complementação da União soma-se ao fundo e fica fora da rosca, como nota)
    $s = $pres.Slides.Add(3, 12); Fundo $s $BRANCO; Titulo $s "Como a educação é financiada"
    $cxR = 200; $cyR = 250; $LARANJA2 = "F4B183"; $CINZA2 = "E5EBF3"
    function Arco($s, $cxA, $cyA, $dA, $espA, $iniA, $fimA, [string]$corA) {  # fatia de anel: ângulos em graus, 0 = topo, sentido horário
        $a = $s.Shapes.AddShape(20, $cxA - $dA / 2, $cyA - $dA / 2, $dA, $dA)
        $a.Adjustments.Item(1) = (($iniA - 90) % 360 + 360) % 360
        $a.Adjustments.Item(2) = (($fimA - 90) % 360 + 360) % 360
        $a.Adjustments.Item(3) = $espA / $dA
        $a.Fill.ForeColor.RGB = (Cor $corA); $a.Fill.Solid(); $a.Line.ForeColor.RGB = (Cor $BRANCO); $a.Line.Weight = 1.5
        $a.Shadow.Visible = 0
    }
    Arco $s $cxR $cyR 200 42 0 90 $BA          # anel interno: 25 para a educação
    Arco $s $cxR $cyR 200 42 90 360 $CINZA2    #               75 livres
    Arco $s $cxR $cyR 290 42 0 18 $LARANJA2    # anel externo: 5 aplicados direto
    Arco $s $cxR $cyR 290 42 18 68.4 $NAVY     #               14 profissionais
    Arco $s $cxR $cyR 290 42 68.4 90 $CE       #               6 outras despesas
    $null = Texto $s "R$ 100" ($cxR - 52) ($cyR - 22) 104 28 22 $NAVY $true $TIT 2
    $null = Texto $s "dos impostos da cesta" ($cxR - 54) ($cyR + 6) 108 14 10 $CINZA $false $CORPO 2
    $null = Texto $s "ICMS, FPM, FPE, IPVA e outros" ($cxR - 54) ($cyR + 20) 108 24 8 $CINZA $false $CORPO 2 $true
    $ch = $s.Shapes.AddShape(20, $cxR - 157, $cyR - 157, 314, 314)  # chave do Fundeb: arco fino por fora dos R$ 14 e R$ 6
    $ch.Adjustments.Item(1) = 18 - 90 + 1; $ch.Adjustments.Item(2) = 0 - 1; $ch.Adjustments.Item(3) = 4 / 314
    $ch.Fill.ForeColor.RGB = (Cor $NAVY); $ch.Fill.Solid(); $ch.Line.Visible = 0; $ch.Shadow.Visible = 0
    $null = Texto $s "Fundeb: R$ 20" 300 98 110 18 13 $NAVY $true
    # legenda em árvore, na ordem em que um valor deriva do outro
    $null = Texto $s "DE CADA R$ 100 DA CESTA DE IMPOSTOS" 430 108 482 18 12 $NAVY $true
    $leg = @(@(0, $CINZA2, "R$ 75", "ficam livres para o estado ou o município"),
             @(0, $BA, "R$ 25", "vão para a educação (MDE):"),
             @(1, $LARANJA2, "R$ 5", "aplicados direto pelo estado ou município"),
             @(1, "grupo", "R$ 20", "vão para o Fundeb, repartido pelas matrículas:"),
             @(2, $NAVY, "R$ 14", "no mínimo (70%), pagam os profissionais"),
             @(2, $CE, "R$ 6", "vão para outras despesas da educação"))
    $passoL = 28; $topoL = 134
    function Ligar($s, $xA, $y1, $y2, [double[]]$ramos) {  # tronco vertical e um ramo horizontal até cada filho
        $v = $s.Shapes.AddLine($xA, $y1, $xA, $y2); $v.Line.ForeColor.RGB = (Cor "A9B7C9"); $v.Line.Weight = 1
        foreach ($yR in $ramos) { $h = $s.Shapes.AddLine($xA, $yR, $xA + 14, $yR); $h.Line.ForeColor.RGB = (Cor "A9B7C9"); $h.Line.Weight = 1 }
    }
    Ligar $s 437 ($topoL + 1 * $passoL + 18) ($topoL + 3 * $passoL + 10) @(($topoL + 2 * $passoL + 10), ($topoL + 3 * $passoL + 10))
    Ligar $s 461 ($topoL + 3 * $passoL + 18) ($topoL + 5 * $passoL + 10) @(($topoL + 4 * $passoL + 10), ($topoL + 5 * $passoL + 10))
    for ($i = 0; $i -lt $leg.Count; $i++) {
        $tp = $topoL + $i * $passoL; $lx = 430 + $leg[$i][0] * 24
        $q = Caixa $s $lx ($tp + 3) 14 14 $(if ($leg[$i][1] -eq "grupo") { $BRANCO } else { $leg[$i][1] }) $false
        if ($leg[$i][1] -eq "grupo") { $q.Line.Visible = -1; $q.Line.ForeColor.RGB = (Cor $NAVY); $q.Line.Weight = 1.5 }
        $tx = $lx + 22
        $null = Texto $s $leg[$i][2] $tx $tp 60 20 15 $NAVY $true $TIT
        $null = Texto $s $leg[$i][3] ($tx + 56) ($tp + 1) (912 - $tx - 56) 20 13 $TINTA
    }
    $c = Caixa $s 430 306 482 38 $CLARO
    $null = Texto $s "+23%" 446 313 70 26 18 $BA $true $TIT
    $null = Texto $s "a União acrescenta, no mínimo, 23% ao Fundeb (VAAF, VAAT e VAAR)" 512 317 390 20 12 $TINTA
    $c = Caixa $s 48 416 612 76 $NAVY
    $null = Texto $s "COTA DO ICMS POR RESULTADOS (EC nº 108/2020)" 68 424 580 14 11 $GELO $true
    $null = Texto $s "Pelo menos 10% do ICMS repassado aos municípios segue a melhoria da aprendizagem" 68 440 580 20 14 $BRANCO $true $TIT
    $null = Texto $s "Os estados repassam 25% do ICMS aos municípios · no Ceará, desde 2007, 18% dessa cota segue a qualidade da educação" 68 466 584 16 11 $GELO
    Rodape $s 3

    # 4 · o que já se sabe e a lacuna
    $s = $pres.Slides.Add(4, 12); Fundo $s $BRANCO; Titulo $s "O que já se sabe e a lacuna"
    $lit = @(@("Entre redes diferentes, associação fraca", "Hanushek (1997, 2003); Menezes-Filho e Amaral (2009)"),
             @("Efeito maior para os mais pobres", "Jackson et al. (2016)"), @("Sem o contexto, redes vulneráveis parecem piores", "Alves e Soares (2013)"))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 296
        $c = Caixa $s $l 108 272 196 $CLARO
        $null = Texto $s "$($i + 1)" ($l + 22) 122 40 30 26 $BA $true $TIT
        $null = Texto $s $lit[$i][0] ($l + 22) 160 230 90 22 $NAVY $true $TIT
        $null = Texto $s $lit[$i][1] ($l + 22) 258 230 40 13 $CINZA $false $CORPO 1 $true
    }
    $c = Caixa $s 48 326 612 112 $NAVY
    $null = Texto $s "LACUNA" 72 344 560 18 12 $GELO $true
    $null = Texto $s "Os dados de gasto, desempenho e contexto já são públicos, mas estão em bases separadas: são raras as ferramentas que os cruzam, rede a rede. É aí que entra este trabalho." 72 364 566 70 16 $BRANCO $true $TIT
    Rodape $s 4

    # 5 · dados, método e indicador
    $s = $pres.Slides.Add(5, 12); Fundo $s $BRANCO; Titulo $s "Dados, método e indicador"
    $passos = @(@("8 bases públicas", "gasto · nota · contexto"), @("2 comparações", "entre municípios e no mesmo município ao longo do tempo"),
                @("Indicador", "nota real × esperada, com o mesmo gasto e contexto"), @("Painel em Power BI", "pares e alertas"))
    for ($i = 0; $i -lt 4; $i++) {
        $l = 48 + $i * 222
        $c = Caixa $s $l 100 196 136 $(if ($i -eq 3) { $NAVY } else { $CLARO })
        $corT = $(if ($i -eq 3) { $BRANCO } else { $NAVY }); $corS = $(if ($i -eq 3) { $GELO } else { $TINTA })
        $null = Texto $s "$($i + 1)" ($l + 18) 110 40 26 22 $(if ($i -eq 3) { $GELO } else { $BA }) $true $TIT
        $null = Texto $s $passos[$i][0] ($l + 18) 142 164 24 17 $corT $true
        $null = Texto $s $passos[$i][1] ($l + 18) 170 164 60 14 $corS
        if ($i -lt 3) { $a = $s.Shapes.AddShape(33, $l + 200, 158, 18, 22); $a.Fill.ForeColor.RGB = (Cor $GELO); $a.Line.Visible = 0 }
    }
    # números do estudo numa faixa fina, cada um centrado na sua coluna
    $c = Caixa $s 48 248 864 52 $CLARO
    $fatos = @(@("2017–2025", "5 edições do Saeb"), @("~5.500", "redes municipais"), @("27", "redes estaduais"))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 288
        $null = Texto $s $fatos[$i][0] $l 252 288 26 20 $NAVY $true $TIT 2
        $null = Texto $s $fatos[$i][1] $l 278 288 16 12 $CINZA $false $CORPO 2
        if ($i -gt 0) { $d = $s.Shapes.AddLine($l, 256, $l, 292); $d.Line.ForeColor.RGB = (Cor "C9D7EA"); $d.Line.Weight = 1 }
    }
    # glossário das 8 bases, em duas colunas (fora do canto inferior direito, reservado ao vídeo)
    $null = Texto $s "AS 8 BASES PÚBLICAS" 48 312 612 16 12 $BA $true
    $bases = @(@("SIOPE (FNDE)", "gastos com educação declarados pelos municípios"),
               @("Siconfi (Tesouro)", "contas dos estados, para o gasto estadual"),
               @("Saeb (Inep)", "prova nacional de Matemática e Português"),
               @("Censo Escolar (Inep)", "matrículas, escolas e infraestrutura"),
               @("Censo Demográfico (IBGE)", "população e alfabetização"),
               @("IDHM (PNUD, FJP e IBGE)", "renda e longevidade de cada estado"),
               @("IPCA (IBGE)", "inflação, para levar os valores a reais de 2025"),
               @("Malha municipal (IBGE)", "contornos dos municípios, para o mapa"))
    for ($i = 0; $i -lt 8; $i++) {
        $l = 48 + ($i % 2) * 316; $tp = 334 + [math]::Floor($i / 2) * 36
        $null = Texto $s $bases[$i][0] $l $tp 300 14 11 $NAVY $true
        $null = Texto $s $bases[$i][1] $l ($tp + 14) 300 16 11 $TINTA
    }
    $null = Texto $s "Scripts feitos com o auxílio de IA, em acordo com a orientadora." 48 482 612 16 11 $CINZA $false $CORPO 1 $true
    Rodape $s 5

    # 6 · o que encontramos: gráfico da correlação (formas) e Ceará × Bahia, num só slide
    $s = $pres.Slides.Add(6, 12); Fundo $s $BRANCO; Titulo $s "O que encontramos"
    $null = Texto $s "1 · GASTO E NOTA: ASSOCIAÇÃO PEQUENA" 48 98 400 16 12 $BA $true
    $null = Texto $s "Correlação entre gasto por aluno e nota (Anos Iniciais, Matemática)" 48 118 400 18 12 $TINTA $true
    $rho = @(@("2017", 0.46), @("2019", 0.41), @("2021", 0.33), @("2023", 0.26), @("2025", 0.16))
    $base = 326; $alt = 160  # 0,50 = 160 pontos de altura
    $eixo = $s.Shapes.AddLine(48, $base, 440, $base); $eixo.Line.ForeColor.RGB = (Cor "D1D5DB"); $eixo.Line.Weight = 1
    for ($i = 0; $i -lt 5; $i++) {
        $h = $rho[$i][1] / 0.5 * $alt; $l = 62 + $i * 78
        $col = Caixa $s $l ($base - $h) 50 $h $(if ($i -eq 4) { $BA } else { $NAVY }) $false
        $null = Texto $s ("{0:0.00}" -f $rho[$i][1]).Replace(".", ",") ($l - 10) ($base - $h - 22) 70 20 14 $(if ($i -eq 4) { $BA } else { $NAVY }) $true $CORPO 2
        $null = Texto $s $rho[$i][0] ($l - 10) ($base + 6) 70 18 12 $CINZA $false $CORPO 2
        if ($i -eq 0 -or $i -eq 4) { $null = Texto $s $(if ($i -eq 0) { "moderada" } else { "fraca" }) ($l - 20) ($base + 21) 90 14 11 $(if ($i -eq 4) { $BA } else { $NAVY }) $true $CORPO 2 $true }
    }
    $c = Caixa $s 48 362 392 80 $NAVY
    $null = Texto $s "+0,2 ponto" 64 380 150 40 26 $BRANCO $true $TIT
    $null = Texto $s "a cada 10% a mais de gasto, no mesmo município; maior em municípios pequenos, no Nordeste e no Norte" 214 374 214 60 12 $GELO
    $null = Texto $s "Associação, e não efeito causal." 48 450 392 18 12 $CINZA $false $CORPO 1 $true
    $null = Texto $s "2 · CEARÁ E BAHIA: GASTO PARECIDO" 480 98 432 16 12 $BA $true
    $null = Texto $s "Redes municipais, 2023 (Anos Iniciais, Matemática)" 480 118 432 18 12 $TINTA $true
    $lados = @(@("Ceará", $CE, "R$ 11.391", "242,4", "90%"), @("Bahia", $BA, "R$ 11.231", "200,1", "38%"))
    for ($i = 0; $i -lt 2; $i++) {
        $l = 480 + $i * 224; $v = $lados[$i]
        $c = Caixa $s $l 144 208 156 $CLARO
        $h = Caixa $s $l 144 208 34 $v[1] $false
        $null = Texto $s $v[0] ($l + 16) 150 180 24 18 $BRANCO $true $TIT
        $null = Texto $s $v[4] ($l + 16) 184 180 46 38 $v[1] $true $TIT
        $null = Texto $s "das redes acima do esperado" ($l + 16) 230 180 16 12 $TINTA
        $null = Texto $s "$($v[2]) por aluno" ($l + 16) 252 180 18 13 $TINTA $true
        $null = Texto $s "$($v[3]) pontos" ($l + 16) 272 180 18 13 $TINTA $true
    }
    $null = Texto $s "Na literatura: cota do ICMS por resultados e assistência técnica no Ceará (não testado aqui)" 480 310 432 40 13 $CINZA $false $CORPO 1 $true
    Rodape $s 6

    # 7 · o painel: Ficha e Pares de Timon lado a lado, com as três perguntas abaixo
    $s = $pres.Slides.Add(7, 12); Fundo $s $BRANCO; Titulo $s "O painel: minha rede e com quem conversar"
    $duas = @(@("caso_a_ficha.png", "+24%  ·  melhor que 98% das redes"), @("caso_a_pares.png", "161 pares  ·  só 1 entrega mais"))
    for ($i = 0; $i -lt 2; $i++) {
        $l = 48 + $i * 472
        $null = Texto $s $duas[$i][1] $l 98 392 26 18 $NAVY $true $TIT
        $p = $s.Shapes.AddPicture((Join-Path $R (Join-Path "docs/resultados/telas" $duas[$i][0])), 0, -1, $l, 130, 392, 220.5)
        $p.Line.Visible = -1; $p.Line.ForeColor.RGB = (Cor "D1D5DB"); $p.Line.Weight = 0.75
    }
    $null = Texto $s "Ficha do município e página Pares: Timon (MA), Anos Iniciais, Matemática, 2023" 48 358 600 16 11 $CINZA $false $CORPO 1 $true
    $null = Texto $s "TRÊS PERGUNTAS PARA O GESTOR" 48 386 600 16 12 $BA $true
    $perg = @("Gastar mais se associa a aprender mais?", "Minha rede entrega o esperado?", "Com quem conversar?")
    $expl = @("o gasto acompanha a nota?", "a nota fica acima ou abaixo da de redes parecidas?", "redes parecidas que entregam mais: referências")
    for ($i = 0; $i -lt 3; $i++) {
        $tp = 408 + $i * 26
        $null = Texto $s "$($i + 1)" 48 $tp 20 22 16 $BA $true $TIT
        $null = Texto $s $perg[$i] 72 ($tp + 1) 290 22 15 $NAVY $true
        $null = Texto $s $expl[$i] 366 ($tp + 3) 300 20 12 $CINZA $false $CORPO 1 $true
    }
    Rodape $s 7

    # 8 · conclusões, contribuições e limitações, e a mensagem principal
    $s = $pres.Slides.Add(8, 12); Fundo $s $BRANCO; Titulo $s "Conclusões, contribuições e limitações"
    $cols = @(@("Conclusões", $NAVY, @(@("PERGUNTA 1", "Há associação, mas pequena: o volume de gasto não basta"), @("PERGUNTA 2", "Redes parecidas entregam resultados muito distintos"))),
              @("Contribuições", $CE, @(@("PRÁTICA", "O painel, com pares e alertas"), @("TEÓRICA", "Evidência de 2017 a 2025, já sob o Novo Fundeb"))),
              @("Limitações", $BA, @(@("", "Associação, não causa"), @("", "Contexto só por UF, até 2024"), @("", "Sem teste com gestores"))))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 296; $k = $cols[$i]; $itens = $k[2]
        $c = Caixa $s $l 104 272 236 $CLARO
        $h = Caixa $s $l 104 272 46 $k[1] $false
        $null = Texto $s $k[0] ($l + 22) 114 230 26 19 $BRANCO $true $TIT
        $passo = 172 / $itens.Count
        for ($j = 0; $j -lt $itens.Count; $j++) {
            $tp = 166 + $j * $passo
            if ($j -gt 0) { $d = $s.Shapes.AddLine($l + 22, $tp - 10, $l + 250, $tp - 10); $d.Line.ForeColor.RGB = (Cor "C9D7EA"); $d.Line.Weight = 1 }
            if ($itens[$j][0]) {
                $null = Texto $s $itens[$j][0] ($l + 22) $tp 230 14 10 $k[1] $true
                $tp += 16
            }
            $null = Texto $s $itens[$j][1] ($l + 22) $tp 230 50 16 $NAVY $true $TIT
        }
    }
    $c = Caixa $s 48 360 612 96 $NAVY
    $null = Texto $s "MENSAGEM PRINCIPAL" 72 376 560 16 12 $GELO $true
    $null = Texto $s "Importa menos quanto se gasta e mais como o recurso é usado" 72 402 570 40 19 $BRANCO $true $TIT
    Rodape $s 8

    # 9 · fechamento
    $s = $pres.Slides.Add(9, 12); Fundo $s $NAVY
    $null = Texto $s "Obrigado!" 48 120 520 70 54 $BRANCO $true $TIT
    $null = Texto $s "O painel e todo o código estão abertos." 48 210 520 30 20 $GELO
    $null = Texto $s "Leia o QR Code ou acesse:" 48 262 520 24 16 $GELO
    $null = Texto $s "github.com/Osodnil/tcc-fea-usp-gasto-publico-educacao-saeb-ideb" 48 290 540 24 16 $BRANCO $true
    $q = Caixa $s 650 96 230 230 $BRANCO
    $null = $s.Shapes.AddPicture((Join-Path $R "docs\resultados\figuras\qrcode_acesso.png"), 0, -1, 663, 109, 204, 204)
    $null = Texto $s "Guilherme Menezes Araújo  ·  Henrique Nogueira Pedro Lindoso  ·  FEA/USP, 2026" 48 470 600 20 13 $GELO

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
