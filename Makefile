# Project-level convenience Makefile

PYTHON := python
SCEN := examples/two_path_v01.yaml

# ensure out/ exists
out:
	mkdir -p out

scan: out
	$(PYTHON) scripts/scan_gauge_phase.py $(SCEN) --save out/scan.png

anim: out
	$(PYTHON) scripts/animate_counts.py $(SCEN) --frames 40 --interval 150 --save out/anim.gif

profile:
	$(PYTHON) scripts/profile_mps.py $(SCEN) --warmup 5 --steps 200

cloud:
	$(PYTHON) scripts/run_demo.py examples/cloud_v01.yaml
