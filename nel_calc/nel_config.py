import json

foldernames = {"config": "config", "samples": "samples"}

filenames = {"config": "config.json"}

default_config = {
        "quantities": {
            "index": {
                "symbol": "index",
                "unit": "unit",
                "name": "index",
                "description": "Index of the measurement",
                "baseType": "int"
            },
            "T": {
                "symbol": "T",
                "unit": "°C",
                "name": "temperature",
                "description": "Temperature of the ionization chamber",
                "baseType": "float"
            },
            "P": {
                "symbol": "P",
                "unit": "kPa",
                "name": "pressure",
                "description": "Pressure of the ionization chamber",
                "baseType": "float"
            },
            "m": {
                "symbol": "m",
                "unit": "nC",
                "name": "charge",
                "description": "Charge measured by the ionization chamber",
                "baseType": "float"
            },
            "k_TP": {
                "symbol": "k_TP",
                "unit": "unit",
                "name": "temperature-pressure correction factor",
                "description": "Temperature-pressure correction factor",
                "baseType": "float"
            },
            "m_corrected": {
                "symbol": "m_corrected",
                "unit": "nC",
                "name": "corrected charge",
                "description": "Corrected charge measured by the ionization chamber",
                "baseType": "float"
            },
        },
        "files": {
            "input_preliminary": {
                "preffix": "input_preliminary",
                "extension": "csv",
                "number": 3,
                "header": [
                    "index",
                    "T",
                    "P",
                    "m"
                ]
            },
            "output_preliminary": {
                "preffix": "output_preliminary",
                "extension": "csv",
                "number": 3,
                "header": [
                    "index",
                    "T",
                    "P",
                    "m",
                    "k_TP",
                    "m_corrected"
                ]
            },
            "summary": {
                "preffix": "summary",
                "extension": "json"
            },
            "input_image": {
                "preffix": "input_image",
                "extension": "dcm"
            },
            "output-image-analysis": {
                "preffix": "output",
                "extension": "pdf"
            },
            "calibration_report": {
                "preffix": "calibration-report",
                "extension": "pdf"
            },
            "pdd_graph": {
                "preffix": "pdd_graph",
                "extension": "pdf"
            }
        },
        "devices": {
            "iViewGT": {
                "name": "iViewGT",
                "type": "epid",
                "brand": "elekta",
                "model": "iViewGT",
                "description": "Elekta iViewGT EPID",
                "capabilities": ["adquisition"],
                "status": ["default"],
                "protocol": "elekta"
                },
            "elekta_precise": {
                "name": "LINAC Elekta Precise",
                "type": "linac",
                "brand": "elekta",
                "model": "precise",
                "description": "Elekta Precise LINAC",
                "capabilities": ["source"],
                "status": ["default"],
                "protocol": "elekta"
                }
            },
        "images": {
            "symmetry": {
                "FilteredFieldLayer": {
                    "field_size_mm": (50, 50)
                },
                "GaussianFilterLayer": {
                    "sigma_mm": 2
                },
                "generate_dicom": {
                    "gantry_angle": 45
                }
            }
        },
        "pdd_graph": {
            "figsize": {
                "x": 8,
                "y": 5
            },
            "xlabel": "Depth (mm)",
            "ylabel": "Absorbed dose (%)",
            "title": "PDD graph",
            "grid": True
        },
        "limits":{
            "PTP": {
                "max": 1.2
            }
        }
    }

def SaveConfigFile(configfilename: str, config: dict) -> int:
    """
    Save the config dictionary into a file with the given name.
    """
    with open(configfilename, "w", encoding = "utf-8") as configFile:
        json.dump(config, configFile, indent = 4)
    
    return 0


def main():
    return 0

if __name__ == "__main__":
    errorCode = main()
    print(f"Program terminated with errorCode: {errorCode}")