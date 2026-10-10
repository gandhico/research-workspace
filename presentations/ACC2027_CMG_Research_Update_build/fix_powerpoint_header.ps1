$deckPath = 'C:\Research\presentations\ACC2027_CMG_PES_Research_Update_2026-08-28.pptx'
$powerPoint = New-Object -ComObject PowerPoint.Application

try {
    $presentation = $powerPoint.Presentations.Open($deckPath, $false, $false, $false)
    $headerShapes = @()
    foreach ($shape in $presentation.SlideMaster.Shapes) {
        if ($shape.Top -ge 0 -and $shape.Top -lt 100 -and $shape.Left -ge 0 -and $shape.Left -lt 1280) {
            $headerShapes += $shape
        }
    }

    foreach ($slideIndex in 2..13) {
        $slide = $presentation.Slides.Item($slideIndex)
        for ($shapeIndex = $slide.Shapes.Count; $shapeIndex -ge 1; $shapeIndex--) {
            $shape = $slide.Shapes.Item($shapeIndex)
            if ($shape.AlternativeText -eq 'NMSU_HEADER_LOCAL') {
                $shape.Delete()
            }
        }

        foreach ($masterShape in ($headerShapes | Sort-Object ZOrderPosition -Descending)) {
            $masterShape.Copy()
            $pasted = $slide.Shapes.Paste()
            foreach ($shape in $pasted) {
                $shape.AlternativeText = 'NMSU_HEADER_LOCAL'
                $shape.ZOrder(1)
            }
        }
    }

    $presentation.Save()
    $presentation.Close()
}
finally {
    $powerPoint.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($powerPoint) | Out-Null
}

Write-Output $deckPath
