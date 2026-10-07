# Clinical Metadata & Data Dictionary (metadata/) — SCAI-SCI Gait Dataset

The **SCAI-SCI Gait Dataset** `metadata/` folder holds the clinical table, the data dictionary, and six
cohort-count tables. Only the data dictionary is in this repository. The table and the
counts are patient data and are distributed through [PhysioNet](https://physionet.org/content/scai-sci-gait-dataset).

| File | In this repository | Content |
|:---|:---:|:---|
| [`data_dictionary.csv`](data_dictionary.csv) | yes | Every column of every table and every field of the C3D and SMPL files (94 rows): `file`, `variable`, `label`, `type`, `units`, `coding`, `standard`. |
| `medical_metadata.csv` | no | The clinical table: 240 rows (one per participant) × 14 columns. |
| `cohort_counts_*.csv` | no | Six attributes released only as counts: `etiology`, `height`, `loi`, `rehab`, `subcat`, `weight`. |

## The clinical table

The table follows the **International SCI Core Data Set v3.0** and its reporting groups.
Demographics, injury characteristics, SCIM III mobility, spasticity, manual muscle testing
and the examination setting were transferred from the medical record into a secuTrial
electronic data capture system under a coded study identifier.

| Column | Content | Coding |
|:---|:---|:---|
| `studyID` | participant number in this release | joins every file of the release |
| `sex` | sex assigned at birth | female; male |
| `age_group_iscos` | age at examination | 15-29; 30-44; 45-59; 60-74; 75+ |
| `neurologic_category` | neurologic category from the NLI and the AIS | C1-4 AIS ABC; C5-8 AIS ABC; T1-S5 AIS ABC; AIS D any level; AIS E (no deficit) |
| `neurological_level_region` | region of the neurological level of injury | C1-4; C5-8; T1-S5; intact |
| `ais_complete` | completeness of the injury | complete (AIS A); incomplete (AIS B-E) |
| `etiology_class` | etiology | traumatic; non-traumatic |
| `years_since_injury_group` | time from injury to the examination | <1; 1-4; 5-9; 10-14; 15-19; 20-24; 25-29; 30+ |
| `lems_band` | ISNCSCI lower-extremity motor score (ten L2–S1 key muscles, 0–50), 10-point band | 0-9; 10-19; 20-29; 30-39; 40-50; empty unless all ten are graded |
| `scim_mobility_band` | SCIM III mobility total (indoors, moderate distances, outdoors, stairs, wheelchair–car and ground–wheelchair transfers) as recorded, 10-point band | 0-9; 10-19; 20-30 |
| `walking_aid` | walking condition during the examination | barefoot; shoes; with aid (crutches or a walking stick) |
| `care_setting` | care setting at the examination | inpatient; outpatient |
| `vibration_sense` | deep (vibration) sensation, lower limbs | normal; deviating |
| `spasticity_mas` | lower-limb spasticity, Modified Ashworth Scale, grouped | 0; 1-1+; 2-4 |

**An empty cell means the value was not recorded.** No other missing-value code is used.

For 3 participants whose row was missing from the assembled clinical table, the row was
derived from the data capture export with the same coding rules. Their injury category is
not recorded.

## What is released only as counts, and what is not released

| Attribute | Where |
|:---|:---|
| Neurological level of injury | `cohort_counts_loi.csv` (the table gives only its region) |
| Height, weight | `cohort_counts_height.csv`, `cohort_counts_weight.csv` |
| Lesion subcategory | `cohort_counts_subcat.csv` |
| Etiology codes of the Core Data Set | `cohort_counts_etiology.csv` (the table gives traumatic / non-traumatic) |
| Time in rehabilitation | `cohort_counts_rehab.csv` |
| Motor and sensory levels per side, individual muscle grades, joint range of motion, SCIM items | not released |

Each count table counts all 240 participants, with "not recorded" as a category of its
own. A band `a-b` holds the values a to b inclusive.

As Core v3.0 prescribes, motor and sensory levels are not reported separately. Because gait and
body shape are biometric, and the clinical demographics in the table are not k-anonymized, the entire
release is available exclusively under credentialed access.

## Linking to the recordings

`studyID` is the number in every file name: `MoCap_Data/mocap<studyID>-<trial>.c3d`,
`SMPL_Data/v<studyID>_…_smpl_sequence.pkl` and `SMPL_Videos/v<studyID>_….mp4`. Every
participant in the table has at least one recording, and every recording has a row
(`has_metadata = 1` in `trials.csv`).

```python
import pandas as pd

DATA = "/path/to/RELEASE_v1.5_SCAI-SCI-Gait"
meta = pd.read_csv(f"{DATA}/metadata/medical_metadata.csv")
gait = pd.read_csv(f"{DATA}/gait_parameters.csv")

print(meta["neurologic_category"].value_counts(dropna=False))
ok = gait[gait["status"] == "ok"].merge(meta, on="studyID")
print(ok.groupby("lems_band")["walking_speed_m_s"].median())
```
