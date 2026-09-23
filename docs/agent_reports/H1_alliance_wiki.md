# H1 — Digital Research Alliance of Canada technical documentation: what the wiki says (for choosing where to run multislice)

Agent: H1. Retrieval date for every fact below: **2026-09-23** (UTC). Source: the Alliance technical
documentation wiki, https://docs.alliancecan.ca/wiki/ . Pages were retrieved as raw wikitext through
`https://docs.alliancecan.ca/mediawiki/index.php?title=<Page>&action=raw` (identical source to the rendered
page) and cached verbatim in
`/tmp/claude-0/-home-user-Holography/9d1f1226-7b90-5531-81d3-dd64f26d9e5a/scratchpad/alliance_wiki_cache/`
(one `.wiki` file per page, filename = page title with spaces→`_` and `/`→`__`, e.g. `Narval__en.wiki`; `manifest.tsv` in that folder gives page title, file, MediaWiki revision id,
last-edit timestamp of the revision read, and retrieval time).

Labels: **SECTION_READ** = I read the cited section of the cited page myself (raw text in cache).
**UNVERIFIED** = could not find/read. **NOT_FOUND** = I looked where it should be and the wiki does not
state it. Short verbatim quotes are in double quotes. Locator format: `Page URL § Section heading`
(the "§ (header table)" locator means the infobox table at the top of the page, before the first heading).
Inferences are marked **INFERENCE** and kept apart from facts.

Status: complete; see §8 for gaps and inconsistencies.

## 1. Which national systems are in service, retired, or being retired

### 1.1 National systems page (status column)
Source: https://docs.alliancecan.ca/wiki/National_systems § "List of compute clusters" (revision 188146, last edited 2025-08-29) — SECTION_READ.

| Cluster | Type (wiki) | Status column (verbatim) |
|---|---|---|
| Béluga | General-purpose | "End of life" |
| Cedar | General-purpose | "End of life" |
| Fir | General-purpose | "In production" |
| Graham | General-purpose | "End of life" |
| Narval | General-purpose | "In production" |
| Niagara | Large parallel | "End of life" |
| Nibi | General-purpose | "In production" |
| Rorqual | General-purpose | "In production" |
| Trillium | Large parallel | "In production" |

Same page § "PAICE clusters" — SECTION_READ: TamIA (Mila), Killarney (Vector Institute), Vulcan (Amii), each "In production".
PAICE is described as "systems dedicated to the current and emerging AI needs of Canada’s research community".

https://docs.alliancecan.ca/wiki/Getting_started (rev 210574, 2026-09-17) — SECTION_READ (cluster list paragraph): "Fir, Narval, Nibi, and Rorqual are general-purpose clusters"; "Trillium is a homogeneous cluster (or supercomputer) designed for large parallel jobs (>1000 cores)."

### 1.2 Retirement dates (Infrastructure renewal page and cluster pages)
Source: https://docs.alliancecan.ca/wiki/Infrastructure_renewal § "System details" and § "System capacity, reductions and outages" (revision 208998, last edited 2026-08-24) — SECTION_READ.

- Replacement map (§ System details table): Rorqual replaces Béluga; Fir replaces Cedar; Trillium replaces "Niagara & Mist"; Nibi replaces Graham. (Narval is not in the table; the SHARCNET webinar blurb in § "User training resources" says "The remaining cluster - Narval - is not having an upgrade this cycle.")
- Cedar: "On September 12, 2025, the '''Cedar''' compute cluster was retired." and "Files stored on '''Cedar''' are already available on '''Fir''' because the two clusters share the same file systems."
- Graham: "On September 1, 2025, the '''Graham''' compute cluster was retired." Files on Graham are available on Nibi (shared file systems).
- Niagara: "On September 30, 2025, the '''Niagara''' compute cluster was retired."
- Mist: "On September 16, 2025, the '''Mist''' compute cluster was retired."
- Béluga: row "January 2026 || June 20, 2026 || Completed || Béluga || End of Service"; "The '''Béluga''' compute service, which was stopped with the deployment of '''Rorqual''', will not return to service." Storage: /scratch decommissioned "February 28, 2026"; "June 20, 2026 – Access to all remaining data will end."

Cluster-page confirmations — SECTION_READ:
- https://docs.alliancecan.ca/wiki/Cedar § (header table): "Availability: SERVICE ENDS 2025 SEPTEMBER 12". (rev 187837, 2025-08-28)
- https://docs.alliancecan.ca/wiki/Graham § (Warning box + header table): "Graham has been retired and replaced by a new system, [[Nibi]]"; "Availability: In production June 2017 until late 2025. SERVICE NOW ENDED." (rev 207009, 2026-07-16)
- https://docs.alliancecan.ca/wiki/B%C3%A9luga/en § (Warning box + header): "The Béluga cluster has been replaced by [[Rorqual/en|Rorqual]]."; "Availability: March, 2019, to June, 2026". (rev 207007, 2026-07-15)
- Niagara: https://docs.alliancecan.ca/wiki/Niagara returns HTTP 404 / MediaWiki reports the page "missing" (checked 2026-09-23), although the National systems table still links to it. UNVERIFIED beyond the Infrastructure-renewal statement above.

**Answer to "Cedar if still up":** Cedar is not up (retired 2025-09-12 per Infrastructure renewal; "End of life" on National systems). Of the clusters Ali named (Fir, Narval, Cedar), Fir and Narval are "In production"; the other in-production national systems are Nibi, Rorqual and Trillium.

### 1.3 In-service availability dates (header tables) — SECTION_READ
- Fir: "Availability date: August 11, 2025" — https://docs.alliancecan.ca/wiki/Fir § (header table) (rev 207144, 2026-07-21)
- Narval: "Availability: since October 2021" — https://docs.alliancecan.ca/wiki/Narval/en § (header table) (rev 203038, 2026-04-16)
- Nibi: "Availability: since 31 July 2025" — https://docs.alliancecan.ca/wiki/Nibi § (header table) (rev 209632, 2026-09-03)
- Rorqual: "Availability: June 19, 2025" — https://docs.alliancecan.ca/wiki/Rorqual/en § (header table) (rev 201614, 2026-04-01)
- Trillium: "Availability: Aug/07 2025" — https://docs.alliancecan.ca/wiki/Trillium § (header table) (rev 210726, 2026-09-22)

### 1.4 PAICE (AI) clusters and eligibility — SECTION_READ
- **TamIA** — https://docs.alliancecan.ca/wiki/TamIA/en (rev 209146, 2026-08-27). Header: "Availability : March 31, 2025", login `tamia.alliancecan.ca`, automation node `robot.tamia.ecpia.ca`, DTN `tamia.alliancecan.ca`. § Access: "To submit compute jobs, you must be a member of an RAP (Resource Allocation Project), which has the prefix <code>aip-</code>"; "The cluster can only be reached from Canada." § Site-specific policies: "The maximum duration of a job is one day (24 hours)."; "Each job must use all 4 GPUs of the servers allocated, i.e. 4 with H100 and 8 with H200."; max 1000 jobs running+pending; compute nodes no internet. Node table: 53 nodes × 4 "NVIDIA HGX H100 SXM 80GB HBM3", 48 cores, 512GB; 12 nodes × 8 "NVIDIA HGX H200 SXM 141GB HBM3", 64 cores, 1024GB; 8 CPU-only nodes. § GPU jobs: "--gpus=h100:4" / "--gpus=h200:8" (whole nodes only).
- **Killarney** — https://docs.alliancecan.ca/wiki/Killarney (rev 209986, 2026-09-10). § Site-specific policies: "Killarney is currently open to Vector affiliated PIs with CCAI Chairs as well as researchers within an AI program at a Canadian university or applying AI methods for their research." § Access: PIs "must be granted an AIP-type RAP (prefix <code>aip-</code> ) by their AI Institution, or by applying for General Access to PAICE Systems"; "Vector enforces geo-blocking". Hardware table: 168 × Dell 750xa, 64 cores, 512 GB, 350 GB SSD, "4 x NVIDIA L40S 48GB"; 10 × Dell XE9680, 48 cores, 2048 GB, 800 GB NVMe, "8 x NVIDIA H100 SXM 80GB". Max walltime: NOT_FOUND on page.
- **Vulcan** — https://docs.alliancecan.ca/wiki/Vulcan (rev 210647, 2026-09-18). § Site-specific policies: "Maximum duration of jobs is 7 days."; "Vulcan is currently open to all researchers doing research on AI or applying AI methods in their research."; "Internet access is not generally available from the compute nodes. A globally available Squid proxy is enabled by default with certain domains whitelisted." § Access: "To be able to submit jobs, you must be a member of an AIP RAP." Hardware: 252 × Dell R760xa, 64 cores, 512 GB, "4 x NVIDIA L40s 48GB".
- INFERENCE (not a wiki statement): all three PAICE clusters require an `aip-` RAP; the wiki does not say whether a physics simulation project without AI methods would qualify; eligibility would have to be established by the PI through the CCDB PAICE declaration. Listed here for completeness only.

## 2. Per-cluster facts for clusters in service (Fir, Narval, Nibi, Rorqual, Trillium)

Cross-cluster pages used in this section (all SECTION_READ, retrieved 2026-09-23):
- LT = https://docs.alliancecan.ca/wiki/Using_node-local_storage § "Amount of space" (rev 188209)
- SFM = https://docs.alliancecan.ca/wiki/Storage_and_file_management § "Filesystem quotas and policies" (per-cluster tabs) (rev 206707)
- SPP = https://docs.alliancecan.ca/wiki/Scratch_purging_policy § "Expiration procedure" (rev 200629)
- JSP = https://docs.alliancecan.ca/wiki/Job_scheduling_policies § "Time limits", § "Number of jobs" (rev 201577)
- RJ = https://docs.alliancecan.ca/wiki/Running_jobs § "Cluster particularities" (rev 209280)
- UGS = https://docs.alliancecan.ca/wiki/Using_GPUs_with_Slurm § "Available GPUs", § "Multi-threaded job" (rev 201140)
- ACS = https://docs.alliancecan.ca/wiki/Allocations_and_compute_scheduling § "Ratios in bundles" (rev 210749 — **edited 2026-09-23 19:23 UTC, i.e. the same day as retrieval**)
- MIG = https://docs.alliancecan.ca/wiki/Multi-Instance_GPU § "Limitations", § "GPU configuration details" (rev 203971)

General statements that apply to all MIG-capable clusters (MIG § Limitations, SECTION_READ):
"<b>requesting more than one MIG instance in a job is not permitted</b>. Such a job will be rejected at submission time."
MIG § GPU configuration details (paraphrase of a bullet list, numbers exact): "An H100 SXM5 GPU has a total of 132 processing units (streaming multiprocessors; "SMs")"; under MIG they are partitioned into one instance of 60 SMs (nvidia_h100_80gb_hbm3_3g.40gb), one of 32 SMs (2g.20gb) and two of 16 SMs (1g.10gb), "leaving eight SMs unassigned and effectively lost"; "What NVidia calls "one eighth" is therefore 4/33 of an H100 GPU, "two eighths" is 8/33 and "three eighths" is 15/33".
MIG § Choosing: "Jobs that use less than half of the computing power of a full GPU and less than half of the available memory should be evaluated and tested on an instance."

### 2.1 Fir (SFU) — page https://docs.alliancecan.ca/wiki/Fir (rev 207144, last edited 2026-07-21) — SECTION_READ
- Login: "fir.alliancecan.ca"; Automation node: "robot.fir.alliancecan.ca"; "Data transfer node (rsync, scp, sftp ...): to be determined" (§ header table). § Site-specific policies: "for tools like rsync and scp, please use the login node." Globus "computecanada#cedar-globus & alliancecan#fir-globus". JupyterHub jupyterhub.fir.alliancecan.ca.
- Access (§ Access): request access in CCDB "via Resources--> Access Systems", select Fir, "It can take up to one hour for your access to be enabled."
- Internet (§ Site-specific policies): "Fir's compute nodes have full access to the internet."
- Walltime (§ Site-specific policies): "Each job should have a duration of at least one hour (at least five minutes for test jobs) and the maximum job duration is 7 days (168 hours)." Crontab not supported. VS Code blocked on login nodes.
- Node table (§ Node characteristics):
  - 864 nodes, 192 cores, "750G or 768000M", 2 x AMD EPYC 9655 (Zen 5), "7.84TB NVMe"
  - 8 nodes, 192 cores, "6000G or 6144000M", 2 x AMD EPYC 9654 (Zen 4), 7.84TB NVMe
  - 160 nodes, 48 cores, "1125G or 1152000M", 1 x AMD EPYC 9454 (Zen 4), 7.84TB NVMe, "4 x NVidia H100 SXM5 (80 GB memory), connected via NVLink"
  - **Internal inconsistency:** § GPU nodes › Layout says "2 NVidia H100 80GB accelerators" then "The 4 node accelerators are interconnected by SXM5." (table says 4 per node. INFERENCE: the "2" may be a per-socket figure carried over from the Rorqual page, whose GPU nodes have 2 sockets each with "2 NVidia H100 accelerators").
- GPU request (§ GPU instances): "One H100-80gb : --gpus=h100:1"; per node "--gpus-per-node=h100:2|3|4"; spread "--gpus=h100:n".
- MIG (§ GPU instances): "Approximately half of the GPU nodes are configured with MIG technology, and only 3 GPU instance sizes are available": 1g.10gb (1/8 compute, 10GB), 2g.20gb (2/8, 20GB), 3g.40gb (3/8, 40GB). Request syntax: "--gpus=nvidia_h100_80gb_hbm3_1g.10gb:1", "--gpus=nvidia_h100_80gb_hbm3_2g.20gb:1", "--gpus=nvidia_h100_80gb_hbm3_3g.40gb:1". (Fir page and UGS show only the long names for Fir; no short synonyms listed for Fir — UGS table "Synonyms for Slurm" column empty for Fir.)
- GPU-node tuning (§ GPU nodes › Performance tuning): "#SBATCH --cpus-per-task=6" keeps threads in one CCD; for NUMA: "--ntasks-per-node=4" "--cpus-per-task=12".
- CPUs/memory per GPU: UGS: "on Fir, no more than 12 CPU cores"; ACS bundle for Fir H100-80gb "12 cores, 288 GB" (bundle) / "12 cores, 280 GB" (recommended); 1g.10gb "1 core, 35 GB" recommended; 2g.20gb "3 cores, 70 GB"; 3g.40gb "6 cores, 140 GB".
- Job-count limit: JSP § Number of jobs names only Narval, Nibi, Rorqual for the 1000-job limit; RJ § Cluster particularities tab "Beluga, Fir, Narval, Nibi, Rorqual": "there is a limit of 1000 jobs, queued and running, per user." **Inconsistent** (Fir included in RJ, not in JSP; Fir page silent).
- Storage (Fir page § Storage): 51PB DDN Lustre, "All mounts share the available storage"; HOME small per-user quota, daily backup; SCRATCH `$HOME/scratch`, "old files are purged automatically"; PROJECT `$HOME/project/${def-project-id}`, daily backup. SFM § Fir tab: Home "50 GB and 500K files per user"; Scratch "20 TB and 1M files per user", "Files older than 60 days are purged."; Project "1 TB and 500K files per group" (RAS up to 40 TB); Nearline "2 TB and 5000 files per group", not mounted on compute nodes.
- $SLURM_TMPDIR: LT table "Fir || 7T || 7.84T".
- Cedar data: Infrastructure renewal: "Files stored on Cedar are already available on Fir because the two clusters share the same file systems."
- GPU profiling: UGS § Profiling: "On Fir and Nibi, GPU profiling like the above technique is not available yet."

### 2.2 Narval (ÉTS Montréal) — page https://docs.alliancecan.ca/wiki/Narval/en (rev 203038, 2026-04-16); French source https://docs.alliancecan.ca/wiki/Narval (rev 203029) — SECTION_READ
- Login "narval.alliancecan.ca"; DTN "narval.alliancecan.ca" (§ header table). Automation node: NOT_FOUND on Narval page (the Automation-MFA page lists it — see §4).
- Internet (§ Site-specific policies): "By policy, Narval's compute nodes cannot access the internet. If you need an exception to this rule, contact technical support".
- Walltime / job count (§ Site-specific policies): "at least one hour (five minutes for test jobs) and you cannot have more than 1000 jobs, running or queued, at any given moment. The maximum duration for a job on Narval is 7 days (168 hours)."
- Node table (§ Node characteristics): 1145 × 64 cores "250G or 256000M" (2 x EPYC 7532, 1 x 960G SSD); 33 × 64 cores "2009G or 2057500M"; 3 × 64 cores "4000G or 4096000M"; **159 GPU nodes × 48 cores, "498G or 510000M", 2 x EPYC 7413, "1 x SSD of 3.84 TB", "4 x NVidia A100SXM4 (40 GB memory), connected via NVLink"**.
- CPU: no AVX-512 ("Narval does not however support the AVX512 instruction set"). StdEnv/2023 default; "previous versions (2016 and 2018) have been blocked intentionally".
- GPU request (§ GPU instances): "--gpus=a100:1"; "--gpus-per-node=a100:2|3|4"; "--gpus=a100:n".
- MIG (§ GPU instances): "Several GPU nodes are configured with Multi-Instance GPU technology. Four sizes are available:" but only three listed: 1g.5gb (1/8, 5 GB) "--gpus=a100_1g.5gb:1"; 2g.10gb (2/8, 10 GB) "--gpus=a100_2g.10gb:1"; 3g.20gb (3/8, 20 GB) "--gpus=a100_3g.20gb:1". **Inconsistency:** "Four sizes" vs three listed; UGS table and ACS bundle table and MIG page example also list `a100_4g.20gb` (4/8, 20 GB) for Narval, whereas ACS § RGUs note says "<b>4g</b> profiles are not available on the clusters." UGS also labels a100_3g.20gb as "2/8" (typo vs 3/8 on Narval page).
- CPUs/memory per GPU: UGS "on Narval, no more than 12 CPU cores"; ACS A100-40gb "12 cores, 124.5 GB" bundle / "12 cores, 124 GB" recommended; 1g.5gb "1 core, 15 GB"; 2g.10gb "3 cores, 31 GB"; 3g.20gb "6 cores, 62 GB"; 4g.20gb "6 cores, 62 GB".
- Storage (§ Storage): HOME Lustre 64 TB total; SCRATCH Lustre 5.7 PB, automated purge; PROJECT Lustre 35 PB. SFM "Narval and Rorqual" tab: Home 50 GB/500K files; Scratch 20 TB/1M files, 60-day purge; Project 1 TB/500K files per group; Nearline "1 TB and 5000 files per group".
- $SLURM_TMPDIR: LT "Narval || 800G || 960G, 3.84T".

### 2.3 Nibi (SHARCNET, Waterloo) — page https://docs.alliancecan.ca/wiki/Nibi (rev 209632, 2026-09-03) — SECTION_READ
- § header table: "SSH login node: nibi.alliancecan.ca"; "Automation node: robot.nibi.alliancecan.ca"; "Data transfer node (rsync, scp, sftp,...): use login nodes"; web interface ondemand.sharcnet.ca; portal portal.nibi.sharcnet.ca.
- Intro: "a general purpose cluster of 134,400 CPU cores and 288 H100 NVIDIA GPUs".
- Internet (§ Site specifics › Internet access): "All nodes on Nibi have internet access, no special firewall permission or proxying is necessary."
- Walltime: not on Nibi page (NOT_FOUND there); JSP § Time limits: "Fir, Narval, Nibi and Rorqual up to 7 days"; RJ tab: "no jobs are permitted longer than 168 hours (7 days)". Job count: JSP § Number of jobs: "On Narval, Nibi and Rorqual, normal accounts can have no more than 1000 jobs in a pending or running state at any time. Each task of a job array counts as one job."
- Node table (§ Node characteristics): 700 × 192 cores "748G or 766000M", 3T local, 2 x Intel 6972P; 10 × 192 cores "6000G or 6144000M", 3T; **36 × 112 cores "2000G or 2048000M", "11T" local, 2 x Intel 8570, "8 x Nvidia H100 SXM (80 GB), connected via NVLink"**; 6 × 96 cores "495G or 507000M", 3T, "4 x AMD MI300A" (unified memory; "should be scheduled as full nodes"; "Code compiled with CUDA will not work"; "As of May 2026 ... there are no modules available with ROCm support").
- GPU instance names (§ GPU instances table): h100 / h100_80gb / nvidia_h100_80gb_hbm3; MIG h100_1g.10gb (= h100_1.10 = h100_10gb = nvidia_h100_80gb_hbm3_1g.10gb), h100_2g.20gb, h100_3g.40gb.
- GPU request: "--gpus=h100:1 or --gpus=h100_80gb:1"; "--gpus-per-node=h100:2|3|4" (the page lists up to 4 although nodes have 8 GPUs — the page does not show `h100:8`); "--gpus=h100:n".
- MIG: "Approximately half of the GPU nodes are configured with MIG technology. Only 3 GPU instance sizes are available": "--gpus=h100_1g.10gb:1", "--gpus=h100_2g.20gb:1", "--gpus=h100_3g.40gb:1".
- CPUs/memory per GPU: UGS "on Nibi, no more than 14 CPU cores"; ACS H100-80gb "14 cores, 250 GB" (bundle and recommended); 1g.10gb "2 cores, 31 GB"; 2g.20gb "4 cores, 62 GB"; 3g.40gb "6 cores, 124 GB" recommended (bundle "7 cores, 125 GB").
- Storage (§ Storage): 25 PB all-SSD VAST for /home, /project, /scratch; "You are "charged" for the apparent size of your files." Scratch (§ /scratch quota): "An 1 TB soft quota on /scratch applies to each user. This soft quota can be exceeded for up to 60 days after which no additional files may be written to /scratch." SPP § Nibi: "There is no time limit, and nothing is automatically deleted" while under the soft limit; "a hard limit of 20TB". SFM Nibi tab: Home 50 GB/500K; Scratch "20 TB hard / 1TB soft and 1M files per user"; Project 1 TB/500K files; Nearline "10 TB and 5000 files per group". /project and /nearline: "User directories are no longer created by default".
- Backups: "snapshot of your files on /home and /project every 30 minutes, and saves the snapshots for two weeks" (`oops` command).
- $SLURM_TMPDIR: LT "Nibi || 3T || 3T, 11T".
- Graham data: available on Nibi (Infrastructure renewal § Graham row).

### 2.4 Rorqual (ÉTS Montréal) — page https://docs.alliancecan.ca/wiki/Rorqual/en (rev 201614, 2026-04-01); French source https://docs.alliancecan.ca/wiki/Rorqual (rev 201609) — SECTION_READ
- § header table: Login "rorqual.alliancecan.ca"; DTN "rorqual.alliancecan.ca"; Automation node "robot.rorqual.alliancecan.ca"; JupyterHub jupyterhub.rorqual.alliancecan.ca; portal metrix.rorqual.alliancecan.ca.
- Access (§ Access): CCDB request, select Rorqual, then accept "Calcul Québec Consent for the collection and use of personal information", "Rorqual Service Level Agreement", "Calcul Québec Terms of Use"; "up to one hour".
- Internet (§ Site-specific policies): "Rorqual's compute nodes cannot access the internet. If you need an exception to this rule, contact technical support".
- Walltime / jobs: "you cannot have more than 1000 jobs, running or queued, at any given moment. The maximum duration is 7 days (168 hours)."
- Node table (§ Node characteristics): 670 × 192 cores "750G or 768000M", 480G SATA SSD; 8 × 192 cores 750G, 3.84TB NVMe; 8 × 192 cores "3013G or 3086250M"; **93 GPU nodes × 64 cores, "498G or 510000M", "1 x NVMe SSD, 3.84TB", 2 x Intel Xeon Gold 6448Y, "4 x NVidia H100 SXM5 (80GB), connected via NVLink"**.
- "To get a larger $SLURM_TMPDIR space, a job can be submitted with --tmp=xG, where x is a value between 370 and 3360." LT: "Rorqual || 375G || 480G, 3.84T".
- GPU instance names, request syntax and MIG: identical wording to Nibi (§ GPU instances): "--gpus=h100:1 or --gpus=h100_80gb:1"; "--gpus-per-node=h100:2|3|4"; MIG "Approximately half of the GPU nodes are configured with MIG technology": "--gpus=h100_1g.10gb:1", "--gpus=h100_2g.20gb:1", "--gpus=h100_3g.40gb:1".
- CPUs/memory per GPU: UGS "on Rorqual, no more than 16 CPU cores"; ACS H100-80gb "16 cores, 124.5 GB" bundle / "16 cores, 124 GB" recommended; 1g.10gb "2 cores, 15 GB"; 2g.20gb "4 cores, 31 GB"; 3g.40gb "8 cores, 62 GB".
- Storage (§ Storage): HOME Lustre 116 TB; SCRATCH Lustre 6.5 PB (`$HOME/links/scratch`), older files purged; PROJECT Lustre 62 PB (`$HOME/links/projects/...`). SFM "Narval and Rorqual" tab (quotas as for Narval above).
- Béluga replaced by Rorqual (Béluga/en Warning box).

### 2.5 Trillium (SciNet, Toronto) — pages https://docs.alliancecan.ca/wiki/Trillium (rev 210726, **edited 2026-09-22**) and https://docs.alliancecan.ca/wiki/Trillium_Quickstart (rev 204255, 2026-05-07) — SECTION_READ
- Hostnames (Trillium § header table): Login CPU "trillium.alliancecan.ca", GPU "trillium-gpu.alliancecan.ca"; DTN "tri-dm{1,2,3,4}.scinet.utoronto.ca"; Automation CPU "robot{1,2,3,4}.scinet.utoronto.ca", GPU "trig-robot1.scinet.utoronto.ca". **Different hostnames in Trillium Quickstart § Logging in:** "ssh -i /PATH/TO/SSH_PRIVATE_KEY MYALLIANCEUSERNAME@trillium.scinet.utoronto.ca" and "...@trillium-gpu.scinet.utoronto.ca". (Both are on the wiki; not verified which resolve.)
- Logging in (Trillium § Logging in): "Password access to the login nodes is disabled. You must use SSH Keys and MFA." "There are separate login and robot nodes for CPU and GPU subclusters." Quickstart: "CPU compute jobs need to be submitted from the CPU login nodes, while GPU compute nodes must be submitted from the GPU login node."
- Internet (§ Internet access): "The internet cannot be reached from compute nodes."
- Node table (Trillium § Node characteristics): CPU 1224 × 192 cores "749G or 767000M" 2 x EPYC 9655; GPU subcluster: **63 × 96 cores "749G or 767000M", 1 x EPYC 9654, "4 x NVidia H100 SXM (80 GB memory)"**; 1 × 96 cores "1498G or 1534M" (sic), "4 x NVidia H200 SXM (141GB memory)"; 52 × 96 cores "2000G or 2048000M", "8 x NVidia B200 SXM (180 GB memory)" with the note "(important: the B200s are not yet available)". Quickstart § Overview: "252 GPUs provided by 63 GPU compute nodes"; CPU nodes "755 GiB / 810 GB of available memory". Quickstart § Memory requests: "768GB" per node — **three different per-node memory figures across the two pages (749G, 755 GiB/810 GB, 768GB).**
- Scheduling granularity (Trillium § Job scheduling): "The resources in the CPU subcluster are scheduled by whole 192-core node." "The resources in the GPU subcluster are scheduled by whole GPU (no "MIG"), or by whole node." Quickstart § Whole node or whole gpu scheduling: single GPU "amounts to a quarter node, with 24 cores and about 188GiB of RAM"; "Trillium does not support MIG ... but you can use Hyper-Q / MPS within your jobs." § GPU Partitions: "you are only allowed to request exactly 1 GPU or a multiple of 4 GPUs. You cannot request --gpus-per-node=2 or 3". Syntax: "For single-GPU jobs, use --gpus-per-node=1." "For whole-node GPU job, use --gpus-per-node=4." (No model specifier in the Trillium examples; UGS lists specifier `h100` for Trillium.)
- Memory: Quickstart § Memory requests are ignored: "single-GPU jobs get 1/4 of the memory, i.e., 188GiB." § Best Practices: "Do not use --mem — memory is fixed per GPU (192 GB) or per node (768 GB)." (188 GiB vs 192 GB — both stated.) ACS Trillium H100-80gb "24 cores, 188 GB".
- Walltime and job limits (Quickstart § Submitting jobs for the GPU subcluster › Partitions and limits): GPU compute: running-job limit "150", submitted-job limit "500", min size "1/4 node (24 cores / 1GPU)", max size "default: 5 nodes (480 cores/20 GPUs)" / "with allocation: 25 nodes (2400 cores/100 GPUs)", min walltime "15 minutes", max walltime "24 hours"; debug: 1 running/1 submitted, "2 hours (1 GPU) - 30 minutes (8 GPUs)". CPU compute: 150 running / 500 submitted, max 24 hours; debug 1 hour. JSP § Time limits: "Trillium accepts jobs of up to 24 hours run-time".
- Account (Quickstart § Default scheduler account): "Jobs will run under your group's RAC allocation, or if one is not available, under a RAS allocation. ... specify the account with the --account=ACCOUNT_NAME option".
- Filesystem write rules (Quickstart § Job output must be written to the scratch file system): home and project "only available for reading on the compute nodes"; submit from $SCRATCH. "Jobs cannot be submitted from compute nodes".
- Storage (Trillium § Home/Project/Scratch; Quickstart § Storage; SFM Trillium tab): $HOME "100 GB per user" (SFM: "100 GB and 1M files per user"), read-only on compute nodes; $PROJECT "1 TB per default group" ("It is not possible to request more project space on Trillium through RAS"); $SCRATCH "25 TB per user" (SFM: "25 TB and 10M files per user"); "There is no purging policy yet, but this is subject to change in the future." (Trillium § Scratch space). **Inconsistent with SPP**, whose § Expiration procedure heading is "Fir, Narval, Rorqual, Trillium" (60-day purge) and gives Trillium's to-delete path "/scratch/t/to_delete/". Nearline = HPSS, "not mounted on the nodes".
- Local disk (Trillium § Local disk space): "Trillium nodes have no local storage." "the $SLURM_TMPDIR environment variable points to a folder on the RAM disk." LT: "$SLURM_TMPDIR is implemented as RAMdisk, so the amount of space available is limited by the memory on the node".
- Debug (Quickstart § Testing and debugging): `debugjob` from GPU login node gives "an interactive session with 1 GPU on a (shared) GPU compute node for two hours"; login-node tests "Use at most 1 GPU"; GPU login node trig-login01 has 4 H100.
- Modules at login (Quickstart § Software): "only the CCconfig, gentoo/2023 and mii modules are loaded ... To get a standard set of compilers and libraries like on the other compute clusters in the Alliance, you load the StdEnv/2023." Single-GPU example loads "module load StdEnv/2023", "module load cuda/12.6", "module load python/3.11.5".

## 3. Software environment

### 3.1 Standard environment (StdEnv)
- https://docs.alliancecan.ca/wiki/Standard_software_environments § "StdEnv/2023" (rev 193658, 2025-10-15) — SECTION_READ: "This is the most recent iteration of our software environment. It uses GCC 12.3.0, Intel 2023.1, and Open MPI 4.1.5 as defaults." "The minimum CPU instruction set supported by this environment is AVX2". Default-module changes include "CUDA 11 => CUDA 12". § intro: "Only versions 2020 and 2023 are actively supported." § StdEnv/2020 warning: "This environment is no longer supported on newer systems".
- Which StdEnv is the login default, per cluster: Narval/en § Software environments: "StdEnv/2023 is the standard software environment on Narval". TamIA/en: "StdEnv/2023 is the standard environment on tamIA". Trillium Quickstart § Software: at login only "CCconfig, gentoo/2023 and mii" are loaded; user must "load the StdEnv/2023". Fir, Nibi, Rorqual pages: default StdEnv NOT_FOUND on the cluster pages. https://docs.alliancecan.ca/wiki/Available_software § Availability warning: "StdEnv/2020 is now deprecated/hidden on the newer systems."
- Available software page tabs: "AVX512 (Fir, Nibi, Rorqual, Trillium, Killarney, tamIA, Vulcan)" and "AVX2 (Narval)" (https://docs.alliancecan.ca/wiki/Available_software § List of globally-installed modules, SECTION_READ; lists transcluded from https://docs.alliancecan.ca/wiki/Modules_avx512 rev 210737 and https://docs.alliancecan.ca/wiki/Modules_avx2 rev 210738, both regenerated 2026-09-22).

### 3.2 Python and CUDA module versions (module list pages; versions are across all StdEnvs, the list does not say which StdEnv each belongs to)
- `python` module versions (Modules_avx512 and Modules_avx2, row "python", identical): "2.7.18, 3.6.10, 3.7.7, 3.7.9, 3.8.2, 3.8.10, 3.9.6, 3.10.2, 3.10.13, 3.11.2, 3.11.5, 3.12.4, 3.13.2, 3.14.2, 3.14.7" — SECTION_READ.
- `cuda` module versions: AVX512 list "10.1, 10.2, 11.0, 11.1.1, 11.2.2, 11.4, 11.7, 11.8, 11.8.0, 12.2, 12.6, 12.9, 13.2, 13.3"; AVX2 (Narval) list "10.1, 10.2, 11.0, 11.1.1, 11.2.2, 11.4, 11.7, 11.8.0, 12.2, 12.6, 12.9, 13.2, 13.3" — SECTION_READ. The CUDA page (https://docs.alliancecan.ca/wiki/CUDA, rev 197795) gives no version list (NOT_FOUND there); its example uses `module load cuda` and, notably, the older `#SBATCH --gres=gpu:1` form. Trillium Quickstart GPU examples use "module load cuda/12.6" and "module load python/3.11.5".
- `scipy-stack` module versions: "2020a, 2020b, 2021a, 2022a, 2023a, 2023b, 2024a, 2024b, 2025a, 2026a, 2026b"; the newest description says "Compatible modules: python/3.14" and lists extensions "matplotlib-3.11.1", "numpy-2.5.3", "scipy-1.18.1", "pandas-3.0.5" (AVX512 list) — SECTION_READ. Python page § SciPy stack: "load a Python version of your choice and then module load scipy-stack".
- **CuPy as a module:** NOT_FOUND (no `cupy` row in Modules_avx512 or Modules_avx2). **CuPy as a wheel:** yes (see 3.4). CUDA page § Troubleshooting › Compute capability: "if you will run your code on a Narval A100 node, the NVidia table gives its compute capability as "8.0"" (H100 compute capability: NOT_FOUND on the wiki).
- No `abtem` module: NOT_FOUND in either module list.

### 3.3 Python page instructions — https://docs.alliancecan.ca/wiki/Python (rev 201101, 2026-03-26) — SECTION_READ
- § Default Python version: the login default "is generally not the one that you should use"; load a module: "module avail python", "module load python/X.Y" (example "3.13").
- § Python version supported: "we provide prebuilt Python packages in our wheelhouse only for the 3 most recent Python versions available on the systems."
- § Creating and using a virtual environment: "virtualenv --no-download ENV", "source ENV/bin/activate", "pip install --no-index --upgrade pip". Warning box: "Do not create your virtual environment under $SCRATCH as it may get partially deleted." Usual location: "/home directory or in one of your /project directories".
- § Installing packages: "pip install numpy --no-index"; "the --no-index option tells pip to not install from PyPI, but instead to install only from locally available packages, i.e. our wheels." "Whenever we provide a wheel for a given package, we strongly recommend to use it by way of the --no-index option." "If you omit the --no-index option, pip will search both PyPI and local packages, and use the latest version available. If PyPI has a newer version, it will be installed instead of our wheel, possibly causing issues."
- § Creating virtual environments inside of your jobs: example job script: "module load python/3.11", "virtualenv --no-download $SLURM_TMPDIR/env", "source $SLURM_TMPDIR/env/bin/activate", "pip install --no-index --upgrade pip", "pip install --no-index -r requirements.txt"; requirements.txt made on a login node with "pip freeze --local > requirements.txt". "**Note**: On Trillium it is recommended to create virtual environments from a login node in HOME and source it in your job script." After the example: "the above instructions require all of the packages you need to be available in the python wheels that we provide ... If the wheel is not available in our wheelhouse, you can pre-download it".
- § Pre-downloading packages (packages not in the wheelhouse): "Run pip download --no-deps tensorboardX" on a login node; "If the filename does not end with none-any, and ends with something like linux_x86_64 or manylinux*_x86_64, the wheel might not function correctly. You should contact Technical support"; then "pip install tensorboardX-1.9-py2.py3-none-any.whl".
- § Installing from a remote repository: "pip install git+https://...@v1.0" — "It is important to use a tag (version) or commit id".
- § Troubleshooting "No matching distribution found for X": "Note also that manylinux_x_y wheels are discarded." § "X is not a supported wheel on this platform": "Some manylinux package can be made available through the wheelhouse."
- § Available wheels: `avail_wheels` command; shows by default only wheels "compatible with the CPU architecture and software environment (StdEnv) that you are currently running on".
- Anaconda: Python § Anaconda → https://docs.alliancecan.ca/wiki/Anaconda/en (rev 196618) — SECTION_READ. Warning box: "Before using Anaconda, we ask that you contact our Technical support"; § Why: binaries "not optimized for the processor architecture", "writes an enormous number of files" in $HOME, "Anaconda is slower than the installation of packages via Python wheels", "modifies the $HOME/.bashrc". § Alternatives: virtualenv first, Apptainer second.
- Login-node internet (explicit statement): NOT_FOUND. The Python page's "Pre-downloading packages ... on a login node" procedure (pip download) implies login nodes reach PyPI — INFERENCE, not a stated fact. Compute-node internet is stated per cluster (Fir/Nibi yes; Narval/Rorqual/Trillium no — see §2).

### 3.4 Available Python wheels — https://docs.alliancecan.ca/wiki/Available_Python_wheels (rev 199180) — SECTION_READ
The page transcludes one table per Python version (pages Wheels3.14 … Wheels3.10, each regenerated 2026-09-23 ~01:20 UTC; revs 210739–210743). Warning box: "Some wheels may not be available in the specific StdEnv you have loaded." The tables are titled "Available wheels across all software environments" — the tables do **not** state StdEnv, CPU architecture or CUDA version per wheel (per-StdEnv: NOT_FOUND; use `avail_wheels` on the cluster).

| package | Python 3.14 | Python 3.13 | Python 3.12 | Python 3.11 | Python 3.10 |
|---|---|---|---|---|---|
| abtem | NOT_FOUND | NOT_FOUND | NOT_FOUND | NOT_FOUND | NOT_FOUND |
| cupy | 14.2.0, 14.1.0, 14.0.1, 13.6.0 | 14.1.0, 14.0.1, 13.6.0 | 14.1.0, 14.0.1, 13.6.0, 13.3.0 | 14.1.0, 14.0.1, 13.6.0, 13.3.0, 12.2.0, 12.0.0 | 13.3.0 … 10.2.0 (7 versions) |
| numba | 0.67.0, 0.65.1, 0.65.0, 0.64.0 | 0.65.1 … 0.61.0 | 0.65.1 … 0.59.1 | 0.65.1 … 0.57.0 | 0.61.0 … 0.55.1 |
| dask | 2026.8.0 (latest of 52) | 2026.8.0 | 2026.8.0 | 2026.8.0 | 2026.8.0 |
| ase | 3.29.0 … 3.16.2 | same | same | same | same |
| numpy | 2.5.3, 2.4.2 | 2.5.3, 2.4.2, 2.3.3, 2.2.2, 2.1.1 | 2.5.3, 2.4.2, 2.3.3, 2.2.2, 2.1.1, 1.26.4 | 2.4.2, 2.3.3, 2.2.2, 2.1.1, 1.26.4, 1.25.2, 1.24.4, 1.24.2, 1.23.2 | 2.2.2 … 1.21.2 |
| scipy | 1.18.1, 1.17.1, 1.17.0 | 1.18.1 … 1.15.1 | 1.18.1 … 1.13.1 | 1.17.1 … 1.10.1 | 1.15.1 … 1.8.0 |
| pyyaml | 6.0.3 | 6.0.3, 6.0.2 | 6.0.3, 6.0.2, 6.0.1 | 6.0.3, 6.0.2, 6.0.1, 6.0, 5.4.1 | 6.0.2, 6.0.1, 6.0, 5.4.1 |
| h5py | 3.16.0, 3.15.1 | 3.16.0, 3.15.0, 3.13.0, 3.12.1 | 3.16.0 … 3.11.0 | 3.16.0 … 3.8.0 | 3.12.0 … 3.6.0 |
| matplotlib | 3.11.1, 3.10.8 | 3.11.1, 3.10.8, 3.10.0 | 3.11.1 … 3.9.0 | 3.11.1 … 2.2.5 | 3.10.0 … 2.2.5 |

(Verbatim rows are in the cached Wheels3.x.wiki files; "…" abbreviates the listed range.)

Note on Python versions: the Python page (§ Python version supported) says prebuilt packages are provided "only for the 3 most recent Python versions available on the systems", while the wheel page still carries tables for 3.10 and 3.11 (and marks only 3.9 and 3.8 "no longer supported"). INFERENCE from the tables: the newest compiled wheels (numpy 2.5.3, scipy 1.18.1, cupy 14.x beyond 14.1.0) appear only for 3.12–3.14, i.e. 3.12, 3.13, 3.14 are the "3 most recent" versions receiving new compiled builds.

Cross-check against abtem 1.0.10's declared dependencies (**external source, not the wiki**: https://pypi.org/pypi/abtem/1.0.10/json read 2026-09-23, SECTION_READ; cached as scratchpad/abtem_1.0.10_pypi.json): requires_python ">=3.11"; requires_dist includes numpy>=2.0.0, pandas, matplotlib>=3.6, pyfftw, scipy, numba, dask (excluding 2025.12.*, 2026.1.0, 2026.1.1; >=2022.12.1), distributed, zarr>=3.1, ase, threadpoolctl, tabulate, ipywidgets, ipympl, tqdm. Distribution files: "abtem-1.0.10-py3-none-any.whl" and sdist. In the wiki wheel tables for Python 3.11/3.12/3.13/3.14 each of these dependencies has a row (e.g. Python 3.12: pyfftw 0.15.1, pandas 3.0.5, distributed 2026.7.1, zarr 3.3.0, threadpoolctl 3.7.0, tabulate 0.10.0, ipywidgets 8.1.9, ipympl 0.9.8). INFERENCE: abtem 1.0.10 itself would have to come via the "Pre-downloading packages" route (its wheel is `none-any`, the form the Python page says is acceptable), with dependencies from the wheelhouse; whether pip resolves all of them with `--no-index` in a given StdEnv must be tested on the cluster with `avail_wheels`.

## 4. Access and automation

### 4.1 Account prerequisites and SSH — https://docs.alliancecan.ca/wiki/SSH (rev 201203) § "What you need" — SECTION_READ
To connect you must "know the name of the machine" (e.g. "fir.alliancecan.ca"), know the username ("not your CCI, like abc-123, nor a CCRI"), "know your password, or have an SSH key", "be registered for multifactor authentication and have your 2nd factor available", and "have requested access to the system" at https://ccdb.alliancecan.ca/me/access_systems . Cluster pages add: Fir/Nibi/Rorqual "It can take up to one hour for your access to be enabled" (Rorqual also requires accepting three Calcul Québec agreements).

### 4.2 SSH key registration (CCDB) — https://docs.alliancecan.ca/wiki/SSH_Keys (rev 188181) § "Installing your key › Using CCDB" — SECTION_READ
- Upload the public key at "https://ccdb.alliancecan.ca/ssh_authorized_keys". "Once your public key is loaded into CCDB this way, you can use it to log in to any of our clusters." "Changes to public keys will often propagate to clusters in a few minutes; in some cases however, it can take up to approximately 30 minutes."
- § Using the authorized_keys file: warning "Support for this method might eventually be withdrawn."
- § Using a key agent: "we strongly suggest using an SSH key agent". § Generating: "provide a strong passphrase ... We recommend 15 characters or more."
- https://docs.alliancecan.ca/wiki/Using_SSH_keys_in_Linux (rev 128702): shows "ssh-keygen -t ed25519" and "ssh-keygen -b 4096 -t rsa".
- Trillium requires keys: Trillium § Logging in "Password access to the login nodes is disabled. You must use SSH Keys and MFA."; Quickstart: "authentication is only allowed via SSH keys that are uploaded to the CCDB", and check the "login node ssh host key fingerprint" on first login.

### 4.3 Multifactor authentication — https://docs.alliancecan.ca/wiki/Multifactor_authentication (rev 207247, 2026-07-28) — SECTION_READ
- § FAQ "I want to disable multifactor authentication": "Multifactor authentication is mandatory. Users cannot disable it. Exceptions can only be granted for automation purposes."
- § Registering factors: Duo Mobile (TOTP apps "Aegis, Google Authenticator, and Microsoft Authenticator are not compatible"), YubiKey, backup codes; "we strongly recommend that you configure at least two options for your second factor".
- § When connecting via SSH: the Duo prompt comes "after you first supply either your password or your SSH key".
- § Configuring your SSH client with ControlMaster › Linux and MacOS (verbatim block):
  ```
  Host HOSTNAME
      ControlPath ~/.ssh/cm-%r@%h:%p
      ControlMaster auto
      ControlPersist 10m
  ```
  "subsequent SSH connections on the same device will reuse the connection of the first session (without asking for authentication), even up to 10 minutes after that first session was disconnected." "the above ControlMaster mechanism ... doesn't work with native Windows" (use WSL; page "Configuring WSL as a ControlMaster relay server", not read).
- § FAQ automated connections: "We are currently deploying a set of login nodes dedicated to automated processes that require unattended SSH connections."
- § FAQ Duo location: Duo blocks IPs from sanctioned countries/regions.

### 4.4 SSH configuration file — https://docs.alliancecan.ca/wiki/SSH_configuration_file (rev 171775, 2025-02-03) — SECTION_READ
Example `Host narval / User username / HostName narval.alliancecan.ca / IdentityFile ~/.ssh/your_private_key`; multi-cluster pattern `Host narval beluga graham cedar ... HostName %h.alliancecan.ca` (page predates the renewal; its cluster list names retired systems). Recommends against enabling ForwardAgent / ForwardX11 by default.
Note: https://docs.alliancecan.ca/wiki/Transferring_data (rev 198470) § Between resources tells users to use agent forwarding `ssh -A` when copying between another cluster and Trillium — the two pages differ in emphasis (not a contradiction: SSH_configuration_file says use agent forwarding "only when you need it").

### 4.5 Automation in the context of MFA — https://docs.alliancecan.ca/wiki/Automation_in_the_context_of_multifactor_authentication (rev 209136, 2026-08-27) — SECTION_READ
- Intro: an unattended workflow "cannot make use of a second authentication factor"; "you must request access to an automation node. An automation node does not require the use of a second factor, but is much more limited than a regular login node".
- § Available only by request: contact technical support and "explain in detail the type of automation you intend to use". Note box (verbatim): "**The automation nodes are designed for predictable workloads. They are not suitable for usage of AI agents.**"
- § Available only through constrained SSH keys: only CCDB-uploaded keys; "SSH keys written in your .ssh/authorized_keys file are not accepted"; "one SSH key per use. Do not reuse the key for interactive login." Keys **must** carry all three constraints: `restrict` (disables port/agent/X11 forwarding and PTY), `from="pattern-list"` (public IPs, at least first three octets, e.g. "x.y.z.*" accepted, "x.y.*.*" not), and `command="COMMAND"`.
- Wrapper scripts (§ Convenience wrapper scripts), under `/cvmfs/soft.computecanada.ca/custom/bin/computecanada/allowed_commands/`: `transfer_commands.sh` (scp/sftp/rsync), `archiving_commands.sh`, `file_commands.sh`, `git_commands.sh`, `slurm_commands.sh` ("allows some Slurm commands, such as squeue, sbatch"; example text: "squeue, scancel, sbatch, scontrol, sq"), `allowed_commands.sh` (all of the above).
- § Automation nodes for each cluster: "Fir: robot.fir.alliancecan.ca", "Narval: robot.narval.alliancecan.ca", "Nibi: robot.nibi.alliancecan.ca", "Rorqual: robot.rorqual.alliancecan.ca", "tamIA: robot.tamia.ecpia.ca", "Trillium: robot2.scinet.utoronto.ca". **Inconsistency:** Trillium page header lists CPU "robot{1,2,3,4}.scinet.utoronto.ca" and GPU "trig-robot1.scinet.utoronto.ca"; Narval's own page does not list its robot node.
- § Using the right key: example `~/.ssh/config` stanza with `identityfile`, `identitiesonly yes`, `requesttty no`. § IPv4 vs IPv6: the `from=` mask must match the address family the client uses (`ssh -4` / `-6`).

### 4.6 Data transfer
- https://docs.alliancecan.ca/wiki/Transferring_data (rev 198470) § intro: "Please use data transfer nodes ... instead of login nodes whenever you are transferring data"; "Globus is the preferred tool for transferring data between systems". Per-cluster DTNs (from §2): Fir "to be determined" (use login node); Narval narval.alliancecan.ca; Nibi "use login nodes"; Rorqual rorqual.alliancecan.ca; Trillium tri-dm{1,2,3,4}.scinet.utoronto.ca.
- Same page § From the World Wide Web: "wget, curl, rclone ... are available on every Alliance cluster by default".

## 5. Slurm usage

### 5.1 Accounts — SECTION_READ
- https://docs.alliancecan.ca/wiki/Job_scheduling_policies § "Priority and fair-share": "Each job is charged to a Resource Allocation Project (RAP). You specify the project with the --account argument to sbatch." RAC grants: account code "will probably begin with rrg- or rpp-"; Rapid Access Service / non-RAC: "will probably begin with def-". "CPU and GPU use are tracked separately" (sshare account names get `_cpu` / `_gpu`). "Past usage is discounted with a half-life of one week".
- https://docs.alliancecan.ca/wiki/Running_jobs § "Accounts and projects": "If you are a member of only one account, the scheduler will automatically associate your jobs with that account." Account string is the CCDB "Group Name" under "My Projects -> My Resources and Allocations". Suggested `~/.bashrc`: "export SLURM_ACCOUNT=def-someuser", "export SBATCH_ACCOUNT=$SLURM_ACCOUNT", "export SALLOC_ACCOUNT=$SLURM_ACCOUNT"; "the environment variable takes priority" over `--account` inside the script.
- PAICE clusters: `aip-` RAPs (see §1.4). Trillium: RAC allocation first, else RAS (§2.5).
- Infrastructure_renewal § RAC: "You will be able to compute with your default allocation (def-xxxxxx) on each new cluster as soon as it goes into service".

### 5.2 Time and memory — SECTION_READ
- Running_jobs § "Use sbatch to submit jobs": "Our policies require that you supply at least a time limit (--time) for each job." Minimal example "reserves 1 core and 256MB of memory for 15 minutes. On Trillium, this job reserves the whole node". Advice: avoid submitting thousands of jobs at once; "Consider using an array job instead, or use sleep to space out calls to sbatch by one second or more."
- Running_jobs § Memory: "On general-purpose (GP) clusters, a default memory amount of 256 MB per core will be allocated unless you make some other request." "--mem=125G is equivalent to --mem=128000M" (binary prefixes).
- Allocations_and_compute_scheduling § Cores equivalent: "On most of our clusters we define a core-equivalent to be 4GB and a core"; charging is by the maximum of cores, memory, RGU bundles.
- Running_jobs § Interactive jobs: "an interactive job with a duration of three hours or less will likely start very soon after submission as we have dedicated test nodes for jobs of this duration."
- Job_scheduling_policies § Time limits (verbatim): "Trillium accepts jobs of up to 24 hours run-time, Fir, Narval, Nibi and Rorqual up to 7 days." "On the general-purpose clusters, longer jobs are restricted to use only a fraction of the cluster by partitions. There are partitions for jobs of 3 hours or less, 12 hours or less, 24 hours (1 day) or less, 72 hours (3 days) or less, 7 days or less". "A shorter job will have more scheduling opportunities than an otherwise-identical longer job." § Backfilling: "Backfilling will primarily benefit jobs with short time limits, e.g. under 3 hours." § Percentage of the nodes: categories base / large-memory / GPU; "by-node" and "by-core" partitions; `partition-stats` shows per-partition node counts ("Please do not write a script which automatically calls partition-stats repeatedly").
- Running_jobs § Do not specify a partition: "you should allow the scheduler to assign a partition to your job based on the resources it requests".

### 5.3 Job counts and arrays — SECTION_READ
- Job_scheduling_policies § Number of jobs: "On Narval, Nibi and Rorqual, normal accounts can have no more than 1000 jobs in a pending or running state at any time. Each task of a job array counts as one job. The limit is applied using Slurm's MaxSubmit parameter."
- Running_jobs § Cluster particularities tab "Beluga, Fir, Narval, Nibi, Rorqual": "no jobs are permitted longer than 168 hours (7 days) and there is a limit of 1000 jobs, queued and running, per user. Production jobs should have a duration of at least an hour." (Includes Fir — inconsistent with Job_scheduling_policies, see §2.1.)
- Trillium: 150 running / 500 submitted (GPU and CPU compute partitions), Quickstart § Partitions and limits.
- Array syntax (Running_jobs § Array job): "#SBATCH --array=1-10", env var `$SLURM_ARRAY_TASK_ID`; "--array=1-100%10" style throttling shown in § Restarting using job arrays ("--array=1-10%1 # Run a 10-job array, one job at a time").
- Maximum array size (MaxArraySize): NOT_FOUND. https://docs.alliancecan.ca/wiki/Job_arrays (rev 149970, last edited 2024-02-09) was fetched and cached but gives no numeric array-size limit (checked by grep for "Max", "limit", digits — see cache).

### 5.4 GPUs with Slurm — https://docs.alliancecan.ca/wiki/Using_GPUs_with_Slurm (rev 201140) — SECTION_READ
- § Introduction: "To request one or more GPUs for a Slurm job, use this form: --gpus-per-node=<model_specifier>:<number>" (e.g. "--gpus-per-node=a100:1"). "--gres=gpu:<model_specifier>:<number>" "may not be supported in the future. We recommend that you replace it in your scripts with --gpus-per-node." Other directives (`--gpus`, `--gpus-per-task`, `--mem-per-gpu`, `--ntasks-per-gpu`) exist but "Our staff do not test all of these".
- § Available GPUs table: Fir H100-80gb `h100` + MIG long names (1/8, 2/8, 3/8); Narval A100-40gb `a100`, `a100_1g.5gb` (1/8), `a100_2g.10gb` (2/8), `a100_3g.20gb` (labelled "2/8"), `a100_4g.20gb` (4/8); Nibi H100-80gb `h100` + MIG (synonyms h100_1g.10gb etc.) and MI300A-128gb `mi300a`; Rorqual H100-80gb `h100` + MIG with synonyms; Trillium H100-80gb `h100`; Killarney `h100`, `l40s`; tamIA `h100`, `h200`; Vulcan `l40s`. Command to list specifiers on a cluster: `sinfo -o "%G"|grep gpu|sed 's/gpu://g'|sed 's/),/\n/g'|cut -d: -f1|sort|uniq`. "If you do not supply a model specifier your job may be rejected or it may be sent to an arbitrary GPU instance ... we strongly recommend that you always provide a specific GPU model specifier".
- § Requesting CPU cores and system memory: "Along with each GPU instance, your job should have a number of CPU cores (default is 1) and some amount of system memory." Recommended maxima → ACS bundle table.
- § Multi-threaded job (bullet items joined; wording verbatim, punctuation normalised): "For each full GPU requested, we recommend" — "on Fir, no more than 12 CPU cores"; "on Narval, no more than 12 CPU cores"; "on Nibi, no more than 14 CPU cores"; "on Rorqual, no more than 16 CPU cores". (Trillium not listed; Trillium Quickstart: 1 GPU = 24 cores, ~188 GiB.)
- § Packing single-GPU jobs: "If you need to run four single-GPU programs or two 2-GPU programs for longer than 24 hours, GNU Parallel is recommended" with `CUDA_VISIBLE_DEVICES=$(({%} - 1))`.
- § Profiling: Narval/Rorqual need `DISABLE_DCGM=1`; "On Fir and Nibi, GPU profiling like the above technique is not available yet."
- MPS: https://docs.alliancecan.ca/wiki/Hyper-Q_/_MPS (rev 188426) fetched and cached (Trillium Quickstart points to it as the alternative to MIG); details not needed here.

### 5.5 Bundle table (per-GPU CPU/memory) — Allocations_and_compute_scheduling § "Ratios in bundles" — SECTION_READ (page edited 2026-09-23 19:23 UTC)
| Cluster | Model/instance | RGU per GPU | Bundle per GPU | Recommended per GPU |
|---|---|---|---|---|
| Fir | H100-80gb | 12.2 | 12 cores, 288 GB | 12 cores, 280 GB |
| Fir | H100-1g.10gb | 1.74 | 1.7 cores, 41 GB | 1 core, 35 GB |
| Fir | H100-2g.20gb | 3.48 | 3.4 cores, 82 GB | 3 cores, 70 GB |
| Fir | H100-3g.40gb | 6.1 | 6 cores, 144 GB | 6 cores, 140 GB |
| Narval | A100-40gb | 4.0 | 12 cores, 124.5 GB | 12 cores, 124 GB |
| Narval | A100-1g.5gb | 0.57 | 1.7 cores, 17.7 GB | 1 core, 15 GB |
| Narval | A100-2g.10gb | 1.14 | 3.4 cores, 35.4 GB | 3 cores, 31 GB |
| Narval | A100-3g.20gb | 2.0 | 6.0 cores, 62.2 GB | 6 cores, 62 GB |
| Narval | A100-4g.20gb | 2.3 | 6.9 cores, 71.5 GB | 6 cores, 62 GB |
| Nibi | H100-80gb | 12.2 | 14 cores, 250 GB | 14 cores, 250 GB |
| Nibi | H100-1g.10gb | 1.74 | 2 cores, 35.7 GB | 2 cores, 31 GB |
| Nibi | H100-2g.20gb | 3.48 | 4 cores, 71.4 GB | 4 cores, 62 GB |
| Nibi | H100-3g.40gb | 6.1 | 7 cores, 125 GB | 6 cores, 124 GB |
| Rorqual | H100-80gb | 12.2 | 16 cores, 124.5 GB | 16 cores, 124 GB |
| Rorqual | H100-1g.10gb | 1.74 | 2.3 cores, 17.7 GB | 2 cores, 15 GB |
| Rorqual | H100-2g.20gb | 3.48 | 4.5 cores, 35.4 GB | 4 cores, 31 GB |
| Rorqual | H100-3g.40gb | 6.1 | 8 cores, 62.2 GB | 8 cores, 62 GB |
| Trillium | H100-80gb | 12.2 | 24 cores, 188 GB | 24 cores, 188 GB |

"users requesting multiple GPUs per node also have to take into account the physical ratios." (§ Ratios in bundles, note.) Multi-Instance_GPU intro: "Using GPU instances is less wasteful, and usage is billed accordingly. Jobs submitted on such instances use less of your allocated priority compared to a full GPU".

### 5.6 Recent scheduling-policy changes — https://docs.alliancecan.ca/wiki/Scheduling_policy_updates (rev 203739, last edited 2026-04-30) — SECTION_READ
- § GPU jobs: "All GPU requests must specify a GPU model or an instance model" — "Fir: 2026-04-06", "Nibi: 2026-04-06", "Narval: (coming soon)", "Rorqual: 2026-04-17".
- § GPU jobs: "Only one MIG instance may be requested at a time" — same dates (Fir/Nibi 2026-04-06, Rorqual 2026-04-17, Narval "coming soon").
- § Accounts: "RAC 2026 accounts activated" Fir/Nibi 2026-04-06, Narval/Rorqual 2026-04-07. § CPU jobs: "(none as of May 1, 2026)".

### 5.7 Job arrays and GPU sharing — SECTION_READ
- https://docs.alliancecan.ca/wiki/Job_arrays § Examples: "sbatch --array=0-7", "--array=1,3,5,7", "--array=1-7:2", "--array=1-100%10 # Allows no more than 10 of the jobs to run simultaneously". § A simple example: "Each task has a separate time limit of 3 hours, and each may start at a different time on a different host." "You should not use a job array to submit tasks with very short run times, e.g. much less than an hour. Tasks with run times of only a few minutes should be grouped into longer jobs using META, GLOST, GNU Parallel, or a shell loop inside a job."
- https://docs.alliancecan.ca/wiki/Hyper-Q_/_MPS § Overview: "MPS is not enabled by default, but it is straightforward to do" (`export CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps`, `export CUDA_MPS_LOG_DIRECTORY=/tmp/nvidia-log`, `nvidia-cuda-mps-control -d`); § GPU farming: MPS "allows you to run multiple instances of the application sharing a single GPU, as long as there is enough of GPU memory for all of the instances".

## 6. FP64 vs FP32 and GPU memory statements on the wiki

- FP64 (double-precision) performance of any in-service GPU: **NOT_FOUND**. Searched all cached pages for "FP64", "double precision", "double-precision": only hits are the retired Cedar page ("Theoretical peak double precision performance of Cedar is 6547 teraflops for CPUs, plus 7434 for GPUs", https://docs.alliancecan.ca/wiki/Cedar) and the retired Graham page (T4 "does not support efficient double precision computations").
- FP32/FP16 relative scores (Allocations_and_compute_scheduling § "Reference GPU Units (RGUs)", SECTION_READ): weights "FP32 performance ratio (with dense matrices on regular GPU cores) 40%", "FP16 performance ratio (with dense matrices on Tensor cores) 40%", "GPU memory size ratio 20%"; A100-40gb is reference (FP32, FP16, memory each 1.0; RGU 4.0). Table "RGU scores for whole GPU models": A100-40gb FP32 1.60 / FP16 1.60 / Memory 0.80 / Combined 4.0; A100-80gb 1.60/1.60/1.60/4.8 (Allocatable "No"); **H100-80gb 5.48 / 5.08 / 1.60 / 12.2**; B200-180gb 6.16 / 11.28 / 3.60 / 21.0. INFERENCE (arithmetic on the wiki's numbers, not a wiki statement): FP32 score 5.48 vs 1.60 means the wiki rates H100 FP32 throughput ≈ 3.4× A100-40gb.
- The RGU text also says "a significant portion of all users are constrained by the amount of memory on the GPU".
- GPU memory per model (node tables, SECTION_READ): Fir H100 "80 GB memory"; Narval A100SXM4 "40 GB memory"; Nibi H100 SXM "80 GB"; Rorqual H100 SXM5 "80GB"; Trillium H100 SXM "80 GB memory" (+ H200 "141GB", B200 "180 GB", "not yet available"); Killarney L40S "48GB", H100 "80GB"; Vulcan L40s "48GB"; tamIA H100 "80GB HBM3", H200 "141GB HBM3"; Nibi MI300A "MI300A-128gb" (Using_GPUs_with_Slurm table; unified with CPU memory per Nibi page).
- MIG memory: H100 instances 10 / 20 / 40 GB; A100 instances 5 / 10 / 20 GB (+ disputed 4g.20gb). SM split for H100 under MIG (60 / 32 / 16 / 16 of 132 SMs) — Multi-Instance_GPU § GPU configuration details.

## 7. Facts relevant to choosing a cluster for a GPU multislice code needing 1 GPU with up to N GB memory per realisation, many independent realisations

Facts only; no recommendation. All retrieved 2026-09-23; SECTION_READ unless marked. Abbreviations for locators as in §2 (UGS, ACS, JSP, RJ, LT, MIG, SPU = Scheduling_policy_updates § GPU jobs).

| | Fir | Narval | Nibi | Rorqual | Trillium (GPU subcluster) |
|---|---|---|---|---|---|
| Status | "In production" (National systems) | "In production" | "In production" | "In production" | "In production" |
| GPU model | H100 SXM5 (Fir § Node characteristics) | A100 SXM4 (Narval/en § Node characteristics) | H100 SXM (Nibi § Node characteristics); also 6 MI300A nodes (ROCm only, whole-node) | H100 SXM5 (Rorqual/en § Node characteristics) | H100 SXM (Trillium § Node characteristics); B200 "not yet available"; 1 H200 node |
| GPU memory per full GPU | "80 GB" | "40 GB" | "80 GB" | "80GB" | "80 GB" |
| GPUs per node | 4 (table; layout text says "2" — inconsistent) | 4 | 8 | 4 | 4 |
| GPU nodes | 160 | 159 | 36 (288 GPUs per intro) | 93 | 63 (Quickstart: "252 GPUs provided by 63 GPU compute nodes") |
| Host memory per GPU node (Slurm) | "1125G or 1152000M" | "498G or 510000M" | "2000G or 2048000M" | "498G or 510000M" | "749G or 767000M" (Quickstart: 768GB/node; 1 GPU gets "188GiB") |
| CPU cores per GPU node | 48 | 48 | 112 | 64 | 96 |
| Recommended cores / host memory per full GPU | 12 cores / 280 GB (ACS); UGS "no more than 12 CPU cores" | 12 / 124 GB (ACS); UGS 12 | 14 / 250 GB (ACS); UGS 14 | 16 / 124 GB (ACS); UGS 16 | 24 cores / 188 GB (ACS), fixed (Quickstart: memory requests ignored) |
| Full-GPU request syntax | `--gpus=h100:1` (Fir § GPU instances) | `--gpus=a100:1` (Narval/en § GPU instances) | `--gpus=h100:1` or `--gpus=h100_80gb:1` (Nibi § GPU instances) | `--gpus=h100:1` or `--gpus=h100_80gb:1` (Rorqual/en § GPU instances) | `--gpus-per-node=1` (Quickstart § Partitions and limits, GPU); only 1 or multiples of 4 |
| Generic form | `--gpus-per-node=<model>:<n>`; `--gres` "may not be supported in the future" (UGS § Introduction). Model specifier mandatory on Fir/Nibi since 2026-04-06, Rorqual since 2026-04-17, Narval "coming soon" (SPU) | | | | |
| MIG instances | "Approximately half of the GPU nodes": 1g.10gb, 2g.20gb, 3g.40gb; `--gpus=nvidia_h100_80gb_hbm3_{1g.10gb,2g.20gb,3g.40gb}:1` (Fir § GPU instances) | "Several GPU nodes": 1g.5gb, 2g.10gb, 3g.20gb via `--gpus=a100_{1g.5gb,2g.10gb,3g.20gb}:1` (Narval/en § GPU instances); 4g.20gb listed in UGS/ACS/MIG example but not on Narval page | "Approximately half": `--gpus=h100_{1g.10gb,2g.20gb,3g.40gb}:1` (Nibi § GPU instances) | "Approximately half": `--gpus=h100_{1g.10gb,2g.20gb,3g.40gb}:1` (Rorqual/en § GPU instances) | None: "scheduled by whole GPU (no "MIG"), or by whole node" (Trillium § Job scheduling); MPS allowed inside a job (Quickstart) |
| Recommended cores / memory per MIG instance (ACS) | 1g: 1 core/35 GB; 2g: 3/70 GB; 3g: 6/140 GB | 1g.5gb: 1/15 GB; 2g.10gb: 3/31 GB; 3g.20gb: 6/62 GB | 1g: 2/31 GB; 2g: 4/62 GB; 3g: 6/124 GB | 1g: 2/15 GB; 2g: 4/31 GB; 3g: 8/62 GB | n/a |
| MIG rule (all) | "requesting more than one MIG instance in a job is not permitted" (MIG § Limitations) | | | | |
| Max walltime | "7 days (168 hours)" (Fir § Site-specific policies) | "7 days (168 hours)" (Narval/en § Site-specific policies) | 7 days (JSP § Time limits; RJ § Cluster particularities; not on Nibi page) | "7 days (168 hours)" (Rorqual/en § Site-specific policies) | "24 hours" (Quickstart GPU partition table; JSP) ; min walltime 15 min |
| Min job length | "at least one hour (at least five minutes for test jobs)" | same | "at least an hour" (RJ tab) | same as Fir | 15 minutes (Quickstart) |
| Walltime partitions (GP clusters) | 3 h / 12 h / 24 h / 72 h / 7 d; "Shorter jobs have access to more resources" (JSP) | same | same | same | n/a (compute + debug partitions) |
| Job count / array limit | 1000 queued+running per user per RJ tab; not listed in JSP § Number of jobs (inconsistent) | 1000 running or queued (Narval/en; JSP) | 1000 pending+running (JSP) | 1000 running or queued (Rorqual/en; JSP) | 150 running, 500 submitted (Quickstart GPU table); default max 5 nodes/20 GPUs, 25 nodes/100 GPUs with allocation |
| Array tasks count as jobs | "Each task of a job array counts as one job" (JSP § Number of jobs) | | | | |
| Max array size (MaxArraySize) | NOT_FOUND | NOT_FOUND | NOT_FOUND | NOT_FOUND | NOT_FOUND |
| Compute-node internet | "full access to the internet" (Fir § Site-specific policies) | "cannot access the internet" (Narval/en) | "All nodes on Nibi have internet access" (Nibi § Internet access) | "cannot access the internet" (Rorqual/en) | "cannot be reached from compute nodes" (Trillium § Internet access) |
| $SLURM_TMPDIR space | "7T" (LT); node disk 7.84TB NVMe | "800G" (LT); GPU node 3.84 TB SSD | "3T" (LT); GPU node 11T | "375G" (LT); `--tmp=xG`, x 370–3360 (Rorqual/en) | RAM disk (Trillium § Local disk space; LT) |
| Scratch quota / purge | 20 TB, 1M files; 60-day purge (SFM, SPP) | 20 TB; 60-day purge | 1 TB soft (60-day grace) / 20 TB hard; no age purge (SFM, SPP § Nibi) | 20 TB; 60-day purge | 25 TB, 10M files (SFM); "no purging policy yet" (Trillium) vs listed under 60-day purge (SPP) |
| Home/Project on compute nodes | "Mounted on Compute Nodes: Yes" (SFM Fir tab) | Yes (SFM Narval and Rorqual tab) | Yes (SFM Nibi tab) | Yes (SFM Narval and Rorqual tab) | read-only: "$HOME cannot be written to from compute jobs", "$PROJECT cannot be written to from compute jobs" (Trillium § Home space, § Project space); write to $SCRATCH |
| Login / DTN / robot | fir.alliancecan.ca / DTN "to be determined" (use login) / robot.fir.alliancecan.ca | narval.alliancecan.ca / narval.alliancecan.ca / robot.narval.alliancecan.ca (Automation page only) | nibi.alliancecan.ca / "use login nodes" / robot.nibi.alliancecan.ca | rorqual.alliancecan.ca / rorqual.alliancecan.ca / robot.rorqual.alliancecan.ca | trillium-gpu.alliancecan.ca (Trillium page) or trillium-gpu.scinet.utoronto.ca (Quickstart) / tri-dm{1..4}.scinet.utoronto.ca / trig-robot1.scinet.utoronto.ca (Trillium page) or robot2.scinet.utoronto.ca (Automation page) |
| GPU profiling via DCGM disable | not available yet (UGS § Profiling) | available with DISABLE_DCGM=1 | not available yet | available with DISABLE_DCGM=1 | NOT_FOUND |
| RGU charged per full GPU (ACS) | 12.2 | 4.0 | 12.2 | 12.2 | 12.2 |

PAICE clusters (TamIA, Killarney, Vulcan) require an `aip-` RAP; TamIA jobs "must use all 4 GPUs" (H100 80 GB) and max 24 h; Vulcan L40S 48 GB, max 7 days; Killarney L40S 48 GB / H100 80 GB, max walltime NOT_FOUND (§1.4).

## 8. What was NOT_FOUND or inconsistent (summary)

NOT_FOUND on the wiki:
1. Maximum job-array size (Slurm MaxArraySize) on any cluster.
2. FP64 performance of H100/A100 (only FP32/FP16 relative scores in the RGU table).
3. Explicit statement that login nodes have internet access / may pip-install from PyPI (implied by the Python page's "Pre-downloading packages ... on a login node").
4. `abtem` in any wheel table (Python 3.10–3.14) or module list; `cupy` as an Lmod module (it exists only as a wheel).
5. Per-wheel StdEnv / CUDA build information in the wheel tables (the page says use `avail_wheels`).
6. Default StdEnv at login stated on the Fir, Nibi, Rorqual pages (stated only for Narval and tamIA; Trillium loads none by default).
7. Max walltime on the Nibi and Killarney pages themselves (Nibi covered by JSP/RJ; Killarney not covered).
8. Fir data-transfer node ("to be determined").
9. The Niagara page (HTTP 404) although still linked from National systems.
10. H100 compute capability (CUDA page gives only the A100 example "8.0").

Inconsistencies (both versions recorded above with locators):
1. Fir GPUs per node: table "4 x NVidia H100" vs layout "2 NVidia H100 80GB accelerators".
2. Fir 1000-job limit: in Running_jobs § Cluster particularities, absent from Job_scheduling_policies § Number of jobs and the Fir page.
3. Narval MIG: "Four sizes are available" but three listed; `a100_4g.20gb` in UGS/ACS/MIG-example vs ACS RGU note "4g profiles are not available on the clusters"; UGS labels `a100_3g.20gb` "2/8".
4. Trillium login hostnames: `trillium(-gpu).alliancecan.ca` (Trillium page) vs `trillium(-gpu).scinet.utoronto.ca` (Quickstart).
5. Trillium automation node: `robot{1,2,3,4}` / `trig-robot1` (Trillium page) vs `robot2.scinet.utoronto.ca` (Automation page).
6. Trillium scratch purge: "no purging policy yet" (Trillium page) vs Trillium grouped with the 60-day purge in Scratch_purging_policy.
7. Trillium memory figures: 749G / 755 GiB / 810 GB / 768 GB per node; 188 GiB vs "192 GB" per GPU; H200 node "1498G or 1534M".
8. Nibi page lists `--gpus-per-node=h100:2|3|4` although nodes have 8 H100.
9. Narval automation node listed on the Automation page but not on the Narval page.
10. SSH_configuration_file example still names retired clusters (beluga, graham, cedar).
11. CUDA page job example uses `--gres=gpu:1` without a model, whereas SPU says model specifiers are now mandatory on Fir/Nibi/Rorqual and UGS deprecates `--gres`.
12. Python page "only for the 3 most recent Python versions" vs wheel tables for 3.10–3.14 (see §3.4 note).

Documents to request from Ali: none required for this report (no paywalled/blocked host). Items only Ali can check on the cluster: his `def-`/`rrg-` account name(s) (CCDB "Group Name"), `avail_wheels` output for the chosen StdEnv, `sinfo -o "%G"` specifiers (command from Using_GPUs_with_Slurm), and the array limit (e.g. `scontrol show config | grep -i MaxArraySize` — standard Slurm command, not taken from the wiki).

Access-policy fact worth flagging to the orchestrator: the Automation page states "The automation nodes are designed for predictable workloads. They are not suitable for usage of AI agents." (§4.5). Interactive login requires MFA ("Multifactor authentication is mandatory. Users cannot disable it.", §4.3).

Status: COMPLETE (2026-09-23).
