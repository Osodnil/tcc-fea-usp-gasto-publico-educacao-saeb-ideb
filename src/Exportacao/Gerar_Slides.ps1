param([string]$Saida = "exportacao\Guilherme_Menezes_Araujo_Henrique_Nogueira_Pedro_Lindoso.pptx",
      [string]$Notas = "",
      [string]$Previa = "")
# Monta pelo próprio PowerPoint (automação COM) os 8 slides do vídeo de apresentação (etapa 6; roteiro em
# docs/roteiro_video.md). As falas do roteiro entram como notas do apresentador. Com -Previa <pasta>, exporta um PNG
# por slide para conferência. Feche o PowerPoint antes de rodar.
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

$notasTxt = @()
if ($Notas) { $notasTxt = Get-Content $Notas -Raw -Encoding UTF8 | ConvertFrom-Json }

$pp = New-Object -ComObject PowerPoint.Application
try {
    $pres = $pp.Presentations.Add(0)  # sem janela; por isso o gráfico do slide 4 é desenhado com formas (AddChart2 exige janela)
    $pres.PageSetup.SlideWidth = 960; $pres.PageSetup.SlideHeight = 540
    $T = "Gasto público por aluno e desempenho no Saeb: uma análise das redes públicas brasileiras com apoio de Business Intelligence"

    # 1 · abertura
    $s = $pres.Slides.Add(1, 12); Fundo $s $NAVY
    $null = Texto $s "TRABALHO DE CONCLUSÃO DE CURSO  ·  ADMINISTRAÇÃO  ·  FEA/USP" 48 64 864 18 12 $GELO $true
    $null = Texto $s $T 48 100 820 150 34 $BRANCO $true $TIT
    $null = Texto $s "Guilherme Menezes Araújo  ·  Henrique Nogueira Pedro Lindoso" 48 290 864 26 20 $BRANCO
    $null = Texto $s "Orientadora: Profa. Adriana Backx Noronha Viana  ·  São Paulo, 2026" 48 322 864 22 15 $GELO
    $b = Caixa $s 48 420 560 52 $NAVY2
    $null = Texto $s "▶  Vídeo: [colar aqui o link do YouTube]" 68 436 520 22 16 $BRANCO $true

    # 2 · problema e pergunta
    $s = $pres.Slides.Add(2, 12); Fundo $s $BRANCO; Titulo $s "O que queremos saber"
    $c = Caixa $s 48 110 380 330 $CLARO
    $null = Texto $s "R$ 339 bi" 76 140 330 70 54 $NAVY $true $TIT
    $null = Texto $s "receita estimada do Fundeb em 2025" 76 216 330 22 16 $TINTA
    $null = Texto $s "Mas os dados de gasto e os de aprendizagem estão em sistemas diferentes, e são raros os portais que comparam, rede a rede, quanto se gasta com quanto se aprende." 76 270 330 130 16 $CINZA
    $c = Caixa $s 460 110 452 330 $NAVY
    $null = Texto $s "PERGUNTA DE PESQUISA" 488 140 400 18 12 $GELO $true
    $null = Texto $s "O gasto público por aluno se associa ao desempenho das redes públicas no Saeb?" 488 172 400 90 22 $BRANCO $true $TIT
    $null = Texto $s "E, considerando o gasto e o contexto de cada rede, quais entregam mais ou menos do que o esperado?" 488 290 400 90 18 $BRANCO
    Rodape $s 2

    # 3 · dados e método
    $s = $pres.Slides.Add(3, 12); Fundo $s $BRANCO; Titulo $s "Dados e método"
    $passos = @(
        @("8 bases públicas", "SIOPE e Siconfi (gasto), Saeb (nota), Censo Escolar, IBGE e IDHM (contexto), IPCA"),
        @("Painéis de dados", "redes municipais e estaduais, 2017 a 2025, valores em R$ de 2025"),
        @("Modelos", "comparação entre municípios e de cada município com ele mesmo; 7 grupos de contexto"),
        @("Painel em Power BI", "desempenho em relação ao esperado, com pares e alertas"))
    for ($i = 0; $i -lt 4; $i++) {
        $l = 48 + $i * 222
        $c = Caixa $s $l 112 196 210 $(if ($i -eq 3) { $NAVY } else { $CLARO })
        $corT = $(if ($i -eq 3) { $BRANCO } else { $NAVY }); $corS = $(if ($i -eq 3) { $GELO } else { $TINTA })
        $null = Texto $s "$($i + 1)" ($l + 20) 128 40 30 26 $(if ($i -eq 3) { $GELO } else { $BA }) $true $TIT
        $null = Texto $s $passos[$i][0] ($l + 20) 168 160 26 18 $corT $true
        $null = Texto $s $passos[$i][1] ($l + 20) 202 160 110 14 $corS
        if ($i -lt 3) { $a = $s.Shapes.AddShape(33, $l + 200, 206, 18, 22); $a.Fill.ForeColor.RGB = (Cor $GELO); $a.Line.Visible = 0 }
    }
    $fatos = @(@("2017–2025", "5 edições do Saeb"), @("~5.500", "redes municipais"), @("27", "redes estaduais"))
    for ($i = 0; $i -lt 3; $i++) {
        $l = 48 + $i * 296
        $null = Texto $s $fatos[$i][0] $l 350 168 34 28 $NAVY $true $TIT
        $null = Texto $s $fatos[$i][1] $l 388 260 22 15 $CINZA
    }
    $null = Texto $s "Scripts desenvolvidos com o auxílio de IA, com autorização da orientadora; todas as decisões estão registradas no repositório público." 48 440 864 36 13 $CINZA $false $CORPO 1 $true
    Rodape $s 3

    # 4 · resultado 1 (gráfico nativo)
    $s = $pres.Slides.Add(4, 12); Fundo $s $BRANCO; Titulo $s "O gasto, sozinho, explica pouco"
    # colunas desenhadas com formas (editáveis no PowerPoint): correlação de Spearman por edição
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
    $null = Texto $s "no Saeb a cada 10% a mais de gasto por aluno, comparando cada município com ele mesmo" 604 176 290 70 15 $GELO
    $c = Caixa $s 580 278 332 152 $CLARO
    $null = Texto $s "Onde a associação aparece" 604 296 290 22 15 $NAVY $true
    $null = Texto $s "Municípios de até 50 mil habitantes, Nordeste e Norte. Nas redes estaduais (27), não é detectável." 604 322 290 90 15 $TINTA
    $null = Texto $s "Resultados de associação, e não de efeito causal." 48 448 500 20 13 $CINZA $false $CORPO 1 $true
    Rodape $s 4

    # 5 · resultado 2: Ceará × Bahia
    $s = $pres.Slides.Add(5, 12); Fundo $s $BRANCO; Titulo $s "Mesmo gasto, resultados diferentes"
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
    $null = Texto $s "O que isso sugere" 668 126 226 24 17 $GELO $true
    $null = Texto $s "A diferença se mantém entre municípios de contexto parecido. A literatura liga o caso do Ceará a incentivos por resultado e à assistência técnica aos municípios: pesa como o recurso é usado, e não só quanto se gasta." 668 160 226 250 15 $BRANCO
    Rodape $s 5

    # 6 · o painel
    $s = $pres.Slides.Add(6, 12); Fundo $s $BRANCO; Titulo $s "O painel: três perguntas para o gestor"
    $perg = @("Gastar mais se associa a aprender mais?", "Minha rede entrega o esperado?", "Com quem conversar?")
    for ($i = 0; $i -lt 3; $i++) {
        $tp = 110 + $i * 92
        $c = Caixa $s 48 $tp 300 78 $(if ($i -eq 2) { $NAVY } else { $CLARO })
        $null = Texto $s "$($i + 1)" 66 ($tp + 20) 30 36 28 $(if ($i -eq 2) { $GELO } else { $BA }) $true $TIT
        $null = Texto $s $perg[$i] 104 ($tp + 18) 230 46 16 $(if ($i -eq 2) { $BRANCO } else { $NAVY }) $true
    }
    $null = Texto $s "Alertas: ⚠ salto atípico de nota e ⚠ rede parcial (prefeitura com menos de metade dos alunos)." 48 390 300 60 13 $CINZA
    $img = $s.Shapes.AddPicture((Join-Path $R "docs\resultados\telas\caso_a_pares.png"), 0, -1, 372, 110, 540, 303.7)
    $img.Line.Visible = -1; $img.Line.ForeColor.RGB = (Cor "D1D5DB"); $img.Line.Weight = 0.75
    $null = Texto $s "Pares de Timon (MA): 24% acima do esperado em 2023, melhor que 98% das redes." 372 422 540 20 13 $CINZA $false $CORPO 1 $true
    Rodape $s 6

    # 7 · conclusões e limitações
    $s = $pres.Slides.Add(7, 12); Fundo $s $BRANCO; Titulo $s "Conclusões e limitações"
    $conc = @("O volume de gasto, sozinho, explica pouco das diferenças de desempenho",
              "Redes com o mesmo gasto podem ter resultados muito diferentes",
              "Comparar com redes parecidas, com alertas, ajuda o gestor a achar referências")
    $lim = @("Associação, e não causalidade", "Contexto socioeconômico só por UF e até 2024", "Painel ainda não testado com gestores")
    $c = Caixa $s 48 104 520 352 $NAVY
    $null = Texto $s "CONCLUSÕES" 72 124 470 18 13 $GELO $true
    for ($i = 0; $i -lt 3; $i++) {
        $tp = 160 + $i * 92
        $null = Texto $s "$($i + 1)" 72 $tp 30 36 28 $GELO $true $TIT
        $null = Texto $s $conc[$i] 112 ($tp + 4) 430 70 18 $BRANCO
    }
    $c = Caixa $s 592 104 320 352 $CLARO
    $null = Texto $s "LIMITAÇÕES" 616 124 270 18 13 $NAVY $true
    for ($i = 0; $i -lt 3; $i++) {
        $null = Texto $s "– $($lim[$i])" 616 (162 + $i * 70) 270 56 16 $TINTA
    }
    Rodape $s 7

    # 8 · fechamento
    $s = $pres.Slides.Add(8, 12); Fundo $s $NAVY
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
