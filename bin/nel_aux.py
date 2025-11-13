import pylinac.calibration.trs398

def GetBaseTypes(config_quantities: dict) -> dict:
    """
    Get the base types of the quantities from the config file.
    """
    baseTypes = dict()
    for key in config_quantities:
        baseTypes[key] = config_quantities[key]["baseType"]
    return baseTypes

def Row2Measurement(row: dict, header: dict, baseTypes: dict) -> dict:
    """
    Convert a row from the CSV file into a measurement dictionary.
    """
    measurement = dict()
    for key in row:
        if baseTypes[key] == "int":
            measurement[key] = int(row[key])
        elif baseTypes[key] == "float":
            measurement[key] = float(row[key])

    return measurement

def ConvertMeasurement(rawMeasurement: dict, oldUnits: dict, newUnits: dict) -> dict:
    """
    Converts raw measurement in old units to new units.
    """
    measurement = rawMeasurement.copy()
    for key in rawMeasurement:
        if oldUnits[key] != newUnits[key]:
            if key == "T":
                # measurement[key] = trs398.convert_temperature(rawMeasurement[key], oldUnits[key], newUnits[key])
                if oldUnits[key] == "°F":
                    measurement[key] = pylinac.calibration.trs398.fahrenheit2celsius(rawMeasurement[key])
                elif oldUnits[key] == "K":
                    measurement[key] = rawMeasurement[key] + 273
            elif key == "P":
                # measurement[key] = trs398.convert_pressure(rawMeasurement[key], oldUnits[key], newUnits[key])
                if oldUnits[key] == "mbar":
                    measurement[key] = pylinac.calibration.trs398.mbar2kPa(rawMeasurement[key])
                elif oldUnits[key] == "mmHg":
                    measurement[key] = pylinac.calibration.trs398.mmHg2kPa(rawMeasurement[key])
            # elif key == "m":
            #     measurement[key] = trs398.convert_charge(rawMeasurement[key], oldUnits[key], newUnits[key])
            # elif key == "k_TP":
            #     measurement[key] = trs398.convert_temperature_pressure_correction_factor(rawMeasurement["T"], rawMeasurement["P"], oldUnits["T"], oldUnits["P"], newUnits["T"], newUnits["P"])
            # elif key == "m_corrected":
            #     measurement[key] = trs398.convert_charge(rawMeasurement[key], oldUnits[key], newUnits[key])
    return measurement

def FindAverage(numberList: list) -> float:
    acum = 0
    for number in numberList:
        acum = acum + number
    # DEBUG: FAIL. With empty value .csv input files.
    return acum / len(numberList)

def FindStdDev(numberList: list) -> float:
    average = FindAverage(numberList)
    acum = 0
    for number in numberList:
        acum = acum + (number - average) ** 2
    return (acum / len(numberList)) ** 0.5

def FindExpectedValue(numberList: list) -> float:
    return FindAverage(numberList)

def main():
    return 0

if __name__ == "__main__":
    errorCode = main()
    print(f"Program terminated with errorCode: {errorCode}")