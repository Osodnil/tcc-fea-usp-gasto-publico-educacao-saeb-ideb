param([Parameter(Mandatory = $true)][string]$Arquivo, [string]$Pdf = "")
# Abre o .docx no Word (sem mostrar), atualiza todos os campos (sumário, listas de figuras, tabelas e quadros) e salva.
# Com -Pdf, exporta também um PDF. Feche o documento no Word antes de rodar.
# Uso: powershell -File src/Exportacao/Atualizar_Campos.ps1 -Arquivo exportacao/TCC_II_FEA_USP_Versao_Final.docx
$caminho = (Resolve-Path $Arquivo).Path
$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
    $d = $w.Documents.Open($caminho, $false, $false)
    $null = $d.Fields.Update()
    foreach ($toc in $d.TablesOfContents) { $toc.Update() }   # sumário e listas: refaz as entradas e as páginas
    $null = $d.Fields.Update()                                # de novo, porque o sumário pode mudar a paginação
    foreach ($toc in $d.TablesOfContents) { $toc.UpdatePageNumbers() }
    "campos TOC: $($d.TablesOfContents.Count); páginas: $($d.ComputeStatistics(2))"
    $d.Save()
    if ($Pdf) { $d.ExportAsFixedFormat($Pdf, 17); "PDF: $Pdf" }
    $d.Close($false)
} finally {
    $w.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($w) | Out-Null
}
