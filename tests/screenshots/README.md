# OCR screenshot fixtures

Drop **full-screen captures** of the game into a folder named after the
capture's resolution:

```
tests/screenshots/
  1280x720/
    student_info.png
    equipment.png
    items.png
    expected.json
  1920x1080/
    student_info.png
    equipment.png
    items.png
    expected.json
```

`tests/test_ocr_screenshots.py` auto-discovers every `<WxH>/` folder and turns
each `*.png` into a parametrised test. The image's own pixel size sets the
`GameAreaManager`, so a single UI region is cropped correctly on every
resolution. Images are matched to a worker by filename prefix:

| Prefix       | Worker               | Fields it extracts                                                                                                                                                      |
| ------------ | -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `student*`   | `student_ocr_worker` | `name`, `level`, `bond`, `star`, `gear1`, `gear2`, `gear3`, `gear_bond`, `ue`, `ue_level`, `ex`, `basic`, `passive`, `sub`, `talent_atk`, `talent_hp`, `talent_healing` |
| `equipment*` | `item_ocr_worker`    | `name`, `count` (Equipment screen)                                                                                                                                      |
| `item*`      | `item_ocr_worker`    | `name`, `count` (Items screen)                                                                                                                                          |  |

## `expected.json`

A flat map of **filename -> expected values**. Only the keys listed are
asserted, so a partial map is fine (e.g. check just the skills for one screenshot).
A value may be a list to accept any of several readings; `null` means the field
should come back empty.

```json
{
    "student_info.png": {
        "name": "Wakamo",
        "level": "90",
        "bond": [
            25,
            26
        ],
        "star": 5,
        "gear1": 9,
        "gear2": 9,
        "gear3": 9,
        "gear_bond": 2,
        "ue": 3,
        "ue_level": 50,
        "ex": 5,
        "basic": 10,
        "passive": 10,
        "sub": 10,
        "talent_atk": [0, null],
        "talent_hp": [0, null],
        "talent_healing": [0, null]
    },
    "equipment.png": {
        "name": "green leaf necklace blueprint",
        "count": "211"
    },
    "items.png": {
        "name": "beginner tech notes choice box",
        "count": "3"
    }
}
```

A folder with screenshots but no `expected.json` (or a screenshot missing from
it) is skipped rather than failed, so you can add images first and fill in the
expectations afterwards. Each screenshot must live in a folder whose name
matches its pixel size, or the test fails with a clear message.

> OCR tests run RapidOCR, which loads `./rapidocr/config.yaml` relative to the
> working directory - run `python -m pytest` from the repository root.