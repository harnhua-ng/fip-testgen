# ==============================================================================
# scripts/run_tc.ps1 — Windows PowerShell Test Runner for lscc_rom
# ==============================================================================
#
# Examples:
#   .\scripts\run_tc.ps1 -tc "01-01"         # Run single testcase
#   .\scripts\run_tc.ps1 -tg "01"            # Run all testcases in Group 01
#   .\scripts\run_tc.ps1 -tc "01-01" -gui    # Launch QuestaSim GUI with waveforms
#
# ==============================================================================

param (
    [string]$tc = "",
    [string]$tg = "",
    [string]$radiant_root = "C:\lscc\radiant\2026.1",
    [switch]$gui
)

$ErrorActionPreference = "Stop"

# 1. Environment & License Setup
$env:LM_LICENSE_FILE     = "$radiant_root\license\license.dat"
$env:SALT_LICENSE_SERVER = "$radiant_root\license\license.dat"
$env:FOUNDRY             = "$radiant_root\ispfpga"
$env:PATH                = "$radiant_root\questasim\win64;$radiant_root\bin\nt64;$env:PATH"

$repo_root = (Split-Path -Parent $PSScriptRoot).Replace("\", "/")
Set-Location $repo_root

# Ensure build & results directories exist
New-Item -ItemType Directory -Force -Path "sim_build" | Out-Null
New-Item -ItemType Directory -Force -Path "results" | Out-Null

# 2. TC Parameter Definitions
function Get-TcConfig {
    param([string]$name)

    $default_init_hex = "$repo_root/testbench/rom_init.hex"

    $configs = @{
        # ── TG-01  Basic Read ────────────────────────────────────────────────────
        "01-01" = @{ regmode="noreg"; rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="mem_file"; init_file=$default_init_hex; init_fmt="hex"; family="common" }
        "01-02" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "01-03" = @{ regmode="noreg"; rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "01-04" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "01-05" = @{ regmode="reg";   rdata=18; rdepth=1024; rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "01-06" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "01-07" = @{ regmode="noreg"; rdata=9;  rdepth=2048; rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }

        # ── TG-02  Read Enable ───────────────────────────────────────────────────
        "02-01" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=1; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "02-02" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=1; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "02-03" = @{ regmode="noreg"; rdata=18; rdepth=1024; rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "02-04" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=1; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }

        # ── TG-03  Read Clock Enable ─────────────────────────────────────────────
        "03-01" = @{ regmode="noreg"; rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "03-02" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "03-03" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "03-04" = @{ regmode="noreg"; rdata=18; rdepth=1024; rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "03-05" = @{ regmode="reg";   rdata=36; rdepth=1024; rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }

        # ── TG-04  Output Clock Enable ───────────────────────────────────────────
        "04-01" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=1; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "04-02" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=1; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "04-03" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=1; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "04-04" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "04-05" = @{ regmode="reg";   rdata=18; rdepth=1024; rst="sync";  out_clk=1; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }

        # ── TG-05  Reset Behavior ────────────────────────────────────────────────
        "05-01" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "05-02" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "05-03" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "05-04" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="async"; out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "05-05" = @{ regmode="reg";   rdata=36; rdepth=512;  rst="async"; out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }
        "05-06" = @{ regmode="noreg"; rdata=36; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_one";  init_file="none";              init_fmt="hex" }

        # ── TG-06  Memory Initialization ─────────────────────────────────────────
        "06-01" = @{ regmode="noreg"; rdata=36; rdepth=512;   rst="sync"; out_clk=0; ecc=0; init_mode="all_zero"; init_file="none";                                init_fmt="hex" }
        "06-02" = @{ regmode="noreg"; rdata=36; rdepth=512;   rst="sync"; out_clk=0; ecc=0; init_mode="all_one";  init_file="none";                                init_fmt="hex" }
        "06-03" = @{ regmode="noreg"; rdata=36; rdepth=512;   rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file=$default_init_hex;                     init_fmt="hex" }
        "06-04" = @{ regmode="noreg"; rdata=18; rdepth=1024;  rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_18_1024.bin"; init_fmt="binary" }
        "06-05" = @{ regmode="noreg"; rdata=9;  rdepth=2048;  rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_9_2048_alt.hex"; init_fmt="hex" }
        "06-06" = @{ regmode="noreg"; rdata=36; rdepth=512;   rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file=$default_init_hex;                     init_fmt="hex" }
        "06-07" = @{ regmode="noreg"; rdata=1;  rdepth=16384; rst="sync"; out_clk=0; ecc=0; init_mode="all_zero"; init_file="none";                                init_fmt="hex" }
        "06-08" = @{ regmode="noreg"; rdata=4;  rdepth=4096;  rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_4_4096.bin";   init_fmt="binary" }

        # ── TG-07  LIFCL EBR Tile Configuration Coverage ─────────────────────────
        "07-01" = @{ regmode="noreg"; rdata=1;  rdepth=2;     rst="sync"; out_clk=0; ecc=0; init_mode="all_zero"; init_file="none";                                init_fmt="hex" }
        "07-02" = @{ regmode="noreg"; rdata=1;  rdepth=16384; rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_1_16384.hex";  init_fmt="hex" }
        "07-03" = @{ regmode="noreg"; rdata=2;  rdepth=8192;  rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_2_8192.hex";   init_fmt="hex" }
        "07-04" = @{ regmode="noreg"; rdata=4;  rdepth=4096;  rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_4_4096.hex";   init_fmt="hex" }
        "07-05" = @{ regmode="noreg"; rdata=9;  rdepth=2048;  rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_9_2048_alt.hex"; init_fmt="hex" }
        "07-06" = @{ regmode="noreg"; rdata=18; rdepth=1024;  rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_18_1024.hex"; init_fmt="hex" }
        "07-07" = @{ regmode="noreg"; rdata=36; rdepth=512;   rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file=$default_init_hex;                     init_fmt="hex" }
        "07-08" = @{ regmode="noreg"; rdata=12; rdepth=512;   rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_12_512.hex";   init_fmt="hex" }

        # ── TG-08  Multi-EBR Cascading ───────────────────────────────────────────
        "08-01" = @{ regmode="noreg"; rdata=36;  rdepth=1024; rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_36_1024.hex";  init_fmt="hex" }
        "08-02" = @{ regmode="noreg"; rdata=36;  rdepth=2048; rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_36_2048.hex";  init_fmt="hex" }
        "08-03" = @{ regmode="noreg"; rdata=72;  rdepth=512;  rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_72_512.hex";   init_fmt="hex" }
        "08-04" = @{ regmode="noreg"; rdata=144; rdepth=512;  rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_144_512.hex";  init_fmt="hex" }
        "08-05" = @{ regmode="noreg"; rdata=72;  rdepth=1024; rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_72_1024.hex";  init_fmt="hex" }
        "08-06" = @{ regmode="noreg"; rdata=36;  rdepth=1024; rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_36_1024.hex";  init_fmt="hex" }
        "08-07" = @{ regmode="noreg"; rdata=36;  rdepth=1024; rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_36_1024.hex";  init_fmt="hex" }
        "08-08" = @{ regmode="reg";   rdata=36;  rdepth=1024; rst="sync"; out_clk=0; ecc=0; init_mode="mem_file"; init_file="$repo_root/testbench/rom_init_36_1024.hex";  init_fmt="hex" }

        # ── TG-09  ECC ───────────────────────────────────────────────────────────
        "09-01" = @{ regmode="noreg"; rdata=32; rdepth=512;  rst="sync";  out_clk=0; ecc=0; init_mode="all_zero"; init_file="none"; init_fmt="hex" }
        "09-02" = @{ regmode="noreg"; rdata=32; rdepth=512;  rst="sync";  out_clk=0; ecc=1; init_mode="all_zero"; init_file="none"; init_fmt="hex" }
        "09-03" = @{ regmode="noreg"; rdata=32; rdepth=512;  rst="sync";  out_clk=0; ecc=1; init_mode="all_zero"; init_file="none"; init_fmt="hex" }
        "09-04" = @{ regmode="noreg"; rdata=64; rdepth=512;  rst="sync";  out_clk=0; ecc=1; init_mode="all_zero"; init_file="none"; init_fmt="hex" }
        "09-05" = @{ regmode="noreg"; rdata=32; rdepth=512;  rst="sync";  out_clk=0; ecc=1; init_mode="all_zero"; init_file="none"; init_fmt="hex" }
        "09-06" = @{ regmode="noreg"; rdata=32; rdepth=512;  rst="sync";  out_clk=0; ecc=1; init_mode="all_zero"; init_file="none"; init_fmt="hex" }
        "09-07" = @{ regmode="noreg"; rdata=32; rdepth=512;  rst="sync";  out_clk=0; ecc=1; init_mode="all_zero"; init_file="none"; init_fmt="hex" }
    }

    $clean_key = $name.Trim().ToUpper().Replace("TC-", "").Replace("TC_", "").Replace("_", "-")
    if ($configs.ContainsKey($clean_key)) {
        return $configs[$clean_key]
    }
    # Default fallback
    return @{ regmode="noreg"; rdata=36; rdepth=512; rst="sync"; out_clk=0; ecc=0; init_mode="all_one"; init_file="none"; init_fmt="hex"; family="lifcl" }
}

# 3. Determine Testcases to Run
$tc_list = @()

if ($tg -ne "") {
    $tg_num = $tg.Trim().ToUpper().Replace("TG-", "").Replace("TG_", "")
    if ($tg_num.Length -eq 1) { $tg_num = "0$tg_num" }
    
    # Collect all matching test cases
    switch ($tg_num) {
        "01" { $tc_list = @("01-01", "01-02", "01-03", "01-04", "01-05", "01-06", "01-07") }
        "02" { $tc_list = @("02-01", "02-02", "02-03", "02-04") }
        "03" { $tc_list = @("03-01", "03-02", "03-03", "03-04", "03-05") }
        "04" { $tc_list = @("04-01", "04-02", "04-03", "04-04", "04-05") }
        "05" { $tc_list = @("05-01", "05-02", "05-03", "05-04", "05-05", "05-06") }
        "06" { $tc_list = @("06-01", "06-02", "06-03", "06-04", "06-05", "06-06", "06-07", "06-08") }
        "07" { $tc_list = @("07-01", "07-02", "07-03", "07-04", "07-05", "07-06", "07-07", "07-08") }
        "08" { $tc_list = @("08-01", "08-02", "08-03", "08-04", "08-05", "08-06", "08-07", "08-08") }
        "09" { $tc_list = @("09-01", "09-02", "09-03", "09-04", "09-05", "09-06", "09-07") }
        default { Write-Error "Unknown test group TG-$tg_num" }
    }
} elseif ($tc -ne "") {
    $clean_tc = $tc.Trim().ToUpper().Replace("TC-", "").Replace("TC_", "").Replace("_", "-")
    $tc_list = @($clean_tc)
} else {
    $tc_list = @("01-01")
}

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Lattice LIFCL ROM Test Runner (PowerShell / QuestaSim)" -ForegroundColor Cyan
Write-Host "  Target: $($tc_list.Count) Testcase(s)" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 4. Map Lattice Radiant Precompiled Simulation Libraries
Write-Host "Mapping Lattice Radiant Precompiled Libraries..." -ForegroundColor Yellow
$radiant_lifcl_lib = "$radiant_root/cae_library/simulation/libs/lifcl".Replace("\", "/")
$radiant_pmi_lib   = "$radiant_root/cae_library/simulation/libs/pmi_work".Replace("\", "/")

if (Test-Path $radiant_lifcl_lib) {
    vmap lifcl $radiant_lifcl_lib | Out-Null
}
if (Test-Path $radiant_pmi_lib) {
    vmap pmi_work $radiant_pmi_lib | Out-Null
}

# 5. Compile DUT and Testbench
Write-Host "Compiling Design & Testbench into sim_build/work..." -ForegroundColor Yellow
vlib sim_build/work | Out-Null
$rtl_src = "$repo_root/rtl/lscc_rom.v"
$top_src = "$repo_root/testbench/testgen_top.v"
$tb_src  = "$repo_root/testbench/tb_rom.v"

vlog -work sim_build/work -sv $rtl_src $top_src $tb_src | Out-Null

# 6. Execute Test Cases
$results = @()
$total_fail = 0

foreach ($test in $tc_list) {
    $cfg = Get-TcConfig $test
    $tc_plusarg = $test.Replace("-", "_")
    $wlf_file   = "$repo_root/results/tc-$test.wlf"
    $log_file   = "$repo_root/results/tc-$test.log"

    $family_val = if ($cfg.family) { $cfg.family } else { "LIFCL" }
    $sim_args = @(
        "-work", "sim_build/work",
        "-L", "lifcl",
        "-L", "pmi_work",
        "-GFAMILY=$family_val",
        "-GRDATA_WIDTH=$($cfg.rdata)",
        "-GRADDR_DEPTH=$($cfg.rdepth)",
        "-GREGMODE=$($cfg.regmode)",
        "-GRESETMODE=$($cfg.rst)",
        "-GOUTPUT_CLK_EN=$($cfg.out_clk)",
        "-GECC_ENABLE=$($cfg.ecc)",
        "-GINIT_MODE=$($cfg.init_mode)",
        "-GINIT_FILE=$($cfg.init_file)",
        "-GINIT_FILE_FORMAT=$($cfg.init_fmt)",
        "-voptargs=+acc",
        "-suppress", "12130",
        "-wlf", $wlf_file,
        "-l", $log_file,
        "+TC=$tc_plusarg"
    )

    Write-Host "`n--> Running TC-$test ($($cfg.regmode), $($cfg.rdata)bx$($cfg.rdepth), $($cfg.init_mode))..." -ForegroundColor Cyan

    if ($gui) {
        Write-Host "Launching QuestaSim GUI..." -ForegroundColor Green
        vsim -gui @sim_args tb_rom
        return
    } else {
        $vsim_output = vsim -c @sim_args -do "log -r /*; run -all; quit" tb_rom
        
        # Check log file for results
        $status = "PASS"
        if (Test-Path $log_file) {
            $log_content = Get-Content $log_file -Raw
            if ($log_content -match "SIMULATION FAILED|Errors: [1-9]|FATAL|Error:") {
                $status = "FAIL"
                $total_fail++
            }
        } else {
            $status = "ERROR"
            $total_fail++
        }

        if ($status -eq "PASS") {
            Write-Host "    TC-$test : PASSED" -ForegroundColor Green
        } else {
            Write-Host "    TC-$test : FAILED (see results/tc-$test.log)" -ForegroundColor Red
        }

        $results += [PSCustomObject]@{
            Testcase = "TC-$test"
            Config   = "$($cfg.rdata)bx$($cfg.rdepth) $($cfg.regmode)"
            InitMode = $cfg.init_mode
            Status   = $status
        }
    }
}

# 7. Summary Table
Write-Host "`n================================================================" -ForegroundColor Cyan
Write-Host "                   TEST EXECUTION SUMMARY                       " -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
$results | Format-Table -AutoSize

if ($total_fail -gt 0) {
    Write-Host "Simulation Run Finished: $total_fail Testcase(s) Failed!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "Simulation Run Finished: All Testcase(s) Passed Successfully!" -ForegroundColor Green
    exit 0
}
