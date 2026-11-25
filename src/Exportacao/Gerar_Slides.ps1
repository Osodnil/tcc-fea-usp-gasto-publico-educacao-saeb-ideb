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

    # 3 · como a educação é financiada (legislação em quatro números e a cota do ICMS)
    $s = $pres.Slides.Add(3, 12); Fundo $s $BRANCO; Titulo $s "Como a educação é financiada"
    $fin = @(@("25%", "da receita de impostos vai para a educação (MDE)"), @("20%", "de uma cesta de impostos forma o Fundeb, repartido pelas matrículas"),
             @("23%", "no mínimo, de complementação da União (VAAF, VAAT e VAAR)"), @("70%", "do Fundeb, no mínimo, paga os profissionais da educação"))
    for ($i = 0; $i -lt 4; $i++) {
        $l = 48 + $i * 222
        $c = Caixa $s $l 108 196 200 $CLARO
        $null = Texto $s $fin[$i][0] ($l + 20) 126 160 50 40 $NAVY $true $TIT
        $null = Texto $s $fin[$i][1] ($l + 20) 186 160 110 15 $TINTA
        if ($i -lt 3) { $a = $s.Shapes.AddShape(33, $l + 200, 196, 18, 22); $a.Fill.ForeColor.RGB = (Cor $GELO); $a.Line.Visible = 0 }
    }
    $c = Caixa $s 48 330 864 110 $NAVY
    $null = Texto $s "COTA DO ICMS POR RESULTADOS (EC nº 108/2020)" 76 350 600 18 12 $GELO $true
    $null = Texto $s "No mínimo 10 pontos da cota dos municípios por resultados educacionais" 76 376 820 28 20 $BRANCO $true $TIT
    $null = Texto $s "No Ceará, desde 2007: 18% da cota, segundo o Índice Municipal de Qualidade Educacional" 76 410 820 20 14 $GELO
    Rodape $s 3

    # 4 · o que a literatura diz
    $s = $pres.Slides.Add(4, 12); Fundo $s $BRANCO; Titulo $s "O que a literatura diz"
    $lit = @(@("Gasto sozinho explica pouco", "Hanushek (1997, 2003); Menezes-Filho e Amaral (2009)"),
             @("Efeito maior para os mais pobres", "Jackson et al. (2016)"), @("O contexto pesa", "Alves e Soares (2013)"))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 296
        $c = Caixa $s $l 108 272 200 $CLARO
        $null = Texto $s "$($i + 1)" ($l + 22) 124 40 30 26 $BA $true $TIT
        $null = Texto $s $lit[$i][0] ($l + 22) 164 230 70 22 $NAVY $true $TIT
        $null = Texto $s $lit[$i][1] ($l + 22) 244 230 50 14 $CINZA $false $CORPO 1 $true
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
    $fatos = @(@("2017–2025", "5 edições do Saeb"), @("~5.500", "redes municipais"), @("27", "redes estaduais"))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 296
        $null = Texto $s $fatos[$i][0] $l 334 168 34 28 $NAVY $true $TIT
        $null = Texto $s $fatos[$i][1] $l 372 260 22 15 $CINZA
    }
    $null = Texto $s "Scripts feitos com o auxílio de IA, em acordo com a orientadora." 48 446 864 20 13 $CINZA $false $CORPO 1 $true
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
    Tela $s "03_eficiencia.png" @(@("3 perguntas", "gastar mais se associa a aprender mais? · minha rede entrega o esperado? · com quem conversar?"),
                                  @("46%", "das redes acima do esperado em 2023")) "Página Desempenho do painel (Anos Iniciais, Matemática, 2023)"
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

    # 11 · conclusões, contribuições e limitações (palavras-chave)
    $s = $pres.Slides.Add(11, 12); Fundo $s $BRANCO; Titulo $s "Conclusões, contribuições e limitações"
    $cols = @(@("CONCLUSÕES", $NAVY, $GELO, $BRANCO, @("Gasto sozinho explica pouco", "Mesmo gasto, resultados diferentes")),
              @("CONTRIBUIÇÕES", $NAVY2, $GELO, $BRANCO, @("Prática: o painel, com pares e alertas", "Teórica: evidência de 2017 a 2025, já sob o Novo Fundeb")),
              @("LIMITAÇÕES", $CLARO, $NAVY, $TINTA, @("Associação, não causa", "Contexto só por UF, até 2024", "Sem teste com gestores")))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 296; $k = $cols[$i]
        $c = Caixa $s $l 104 272 352 $k[1]
        $null = Texto $s $k[0] ($l + 22) 124 230 18 13 $k[2] $true
        for ($j = 0; $j -lt $k[4].Count; $j++) {
            $null = Texto $s "– $($k[4][$j])" ($l + 22) (162 + $j * 90) 232 80 $(if ($i -lt 2) { 20 } else { 18 }) $k[3] ($i -lt 2) $(if ($i -lt 2) { $TIT } else { $CORPO })
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
