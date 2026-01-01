import os
import sys
import json
import csv
import pathlib

import pylinac.calibration.trs398
import pylinac.core.image_generator.layers
import pylinac
import click
import pandas as pd
import matplotlib.pyplot as plt

import nel_calc.nel_config
import nel_calc.nel_aux
import nel_calc.customSim

def validate_config_path_exclusive_option(ctx, param, value):
    """Validate that config_path is not used with other options."""
    click.echo(f"Context: {ctx}")
    click.echo(f"Parameter: {param}")
    click.echo(f"Value: {value}")
    click.echo(f'Params: {ctx.params if ctx else "No context"}')

    if value:
        for other_param in ctx.params:
            if other_param == "config_path":
                raise click.UsageError(f"Options '{param.name}' and '{other_param}' cannot be used together.")

    return value

def validate_mutually_exclusive_options(ctx, param, value):
    """Validate that only one of the options is used."""
    click.echo(f"Context: {ctx}")
    click.echo(f"Parameter: {param}")
    click.echo(f"Value: {value}")
    click.echo(f'Params: {ctx.params if ctx else "No context"}')
    
    if value:
        for other_param in ctx.params:
            if other_param != param.name and ctx.params[other_param]:
                raise click.UsageError(f"Options '{param.name}' and '{other_param}' cannot be used together.")
            
    return value

program_folder = pathlib.Path(__file__).parent.parent.resolve()
samples_folder = program_folder / nel_calc.nel_config.foldernames["samples"]

@click.group()
@click.version_option("0.2.0", prog_name="nel_calc")
def cli():
    """Main command line interface for the program."""
    pass

#command to create a config file
@click.command()
@click.argument("filename", type=click.Path(file_okay=True, dir_okay=False), required=True)
def create_config(filename):
    """Create a config file."""    
    # Check if the file already exists.
    if pathlib.Path(filename).exists():
        raise click.BadParameter("File already exists. Please choose a different name or delete the existing file.")
    with open(filename, "w", encoding="utf-8") as configFile:
        json.dump(nel_calc.nel_config.default_config, configFile, indent=4)
        click.echo(f"Config file {filename} created.")
    
    sys.exit(0)

#command to create image for 2D profiling
@click.command()
@click.argument("filename", type=click.Path(file_okay=True, dir_okay=False), required=True)
@click.option("--field-size-mm", type=click.Tuple([float, float]), callback=validate_config_path_exclusive_option, help="Field size in mm.")
@click.option("--sigma_mm", type=float, callback=validate_config_path_exclusive_option, help="Sigma in mm for the Gaussian filter.")
@click.option("--gantry-angle", type=float, callback=validate_config_path_exclusive_option, help="Gantry angle in degrees.")
@click.option("--epid", type=str, callback=validate_config_path_exclusive_option, help="Name of the EPID that will be simulated.")
@click.option("--config", type=click.Path(exists=True, file_okay=True), callback=validate_config_path_exclusive_option, help="Path to the config file.")
def create_image_planar(filename, field_size_mm, sigma_mm, gantry_angle, epid, config):
    """Create planar image for 2D profiling."""

    # Load the config file.
    if config:
        with open(config, "r", encoding = "utf-8") as configFile:
            configJSON = json.load(configFile)
    
        field_size_mm=configJSON["images"]["symmetry"]["FilteredFieldLayer"]["field_size_mm"]
        sigma_mm=configJSON["images"]["symmetry"]["GaussianFilterLayer"]["sigma_mm"]
        gantry_angle=configJSON["images"]["symmetry"]["generate_dicom"]["gantry_angle"]
        for device in configJSON["devices"]:
            if configJSON["devices"][device]["type"] == "epid":
                deviceStatus = configJSON["devices"][device]["status"]
                if "default" in deviceStatus:
                    epid = configJSON["devices"][device]["name"]
                    break
                else:
                    raise LookupError("No default EPID found in the config file.")
            else:
                raise KeyError("No EPID found in the config file.")
    else:
        #Check if all the parameters are provided.
        if field_size_mm is None or sigma_mm is None or gantry_angle is None or epid is None:
            raise click.BadParameter("All parameters are required.")
    
    #Load the appropiated epid class.
    if epid == "iViewGT":
        iViewGT0 = nel_calc.customSim.iViewGTImage()
    else:
        raise ValueError(f"Unknown EPID name for class instance: {epid}.")
    
    iViewGT0.add_layer(pylinac.core.image_generator.layers.FilteredFieldLayer(field_size_mm=field_size_mm))
    iViewGT0.add_layer(pylinac.core.image_generator.layers.GaussianFilterLayer(sigma_mm=sigma_mm))
    iViewGT0.generate_dicom(file_out_name=filename, gantry_angle=gantry_angle)

    click.echo("Sample images created.")
    sys.exit(0)

#create calibration command
@click.command()
@click.argument("filename", type=click.Path(file_okay=True, dir_okay=False), required=True)
def create_calibration(filename):
    """Create a calibration file."""
    # Check if the file already exists.
    # if pathlib.Path(filename).exists():
    #    raise click.BadParameter("File already exists. Please choose a different name or delete the existing file.")

    with open(filename, "w", encoding="utf-8") as calibrationFile:
        json.dump(nel_calc.nel_aux.calibration_data, calibrationFile, indent=4, ensure_ascii=False)
        click.echo(f"Calibration file {filename} created.")
    
    sys.exit(0)

#analyze-preliminary command    
@click.command()
#@click.argument("filenames", nargs=-1, type=click.Path(exists=True, file_okay=True), required=True)
@click.option("--input-dir", type=click.Path(exists=True, dir_okay=True), help="Path of input file directory.")
@click.option("--output-dir", type=click.Path(exists=True, dir_okay=True), help="Path of output file directory.")
@click.option("--input-preffix", type=click.STRING, help="Input fileName preffix.")
@click.option("--output-preffix", type=click.STRING, help="Output fileName preffix.")
@click.option("--filetype", type=click.STRING, help="FileType of the input and output files.")
@click.option("--summary", type=click.Path(exists=False, file_okay=True), help="FileName of summary file.")
@click.option("--config", type=click.Path(exists=True, file_okay=True), help="Config filename.")
def analyze_preliminary(config, input_dir, output_dir, input_preffix, output_preffix, filetype, summary):
    """Analyze calibration preliminary data about measurements."""

    # Load the config file.
    with open(config, "r", encoding = "utf-8") as configFile:
        configJSON = json.load(configFile)

    # Base types for the quantities.
    default_baseTypes = nel_calc.nel_aux.GetBaseTypes(configJSON["quantities"])

    #Obtaining the units that will be used in the output files.
    new_input_units = {key: configJSON["quantities"][key]["unit"] for key in configJSON["files"]["input_preliminary"]["header"]}
    output_header = configJSON["files"]["output_preliminary"]["header"]
    old_output_units = {key: configJSON["quantities"][key]["unit"] for key in output_header}

    # Filenames for the output files.
    #summary = f"{configJSON["files"]["summary"]["preffix"]}.{configJSON["files"]["summary"]["extension"]}"
    #output_preffix = f"{configJSON["files"]["output_preliminary"]["preffix"]}"

    #limits
    max_PTP = configJSON["limits"]["PTP"]["max"]

    # Getting the input filenames.
    input_suffix = f".{filetype}"
    filenames = list()
    for file in pathlib.Path(input_dir).iterdir():
        if file.is_file():
            if file.name.startswith(input_preffix) and file.suffix == input_suffix:
                filenames.append(str(file.resolve()))
    if len(filenames) == 0:
        print("Cannot find input files.")
        return
        #raise FileNotFoundError

    # from files to rawMeasurement_list_tries
    # Read the files and convert them to rawMeasurement_list_tries
    rawMeasurement_list_tries = list()
    for filename in filenames:    
        with open(filename, "r", encoding = "utf-8") as csvFile:
            csvDictReader = csv.DictReader(csvFile)
            input_header = csvDictReader.fieldnames # Getting the current header in first line
            old_input_units = next(csvDictReader) # Getting the units in second line
            rawMeasurement_list = list()
            for row in csvDictReader: # Getting the values
                rawMeasurement = nel_calc.nel_aux.Row2Measurement(row=row, header=input_header, baseTypes=default_baseTypes)
                rawMeasurement_list.append(rawMeasurement.copy())
        rawMeasurement_list_tries.append(rawMeasurement_list.copy())

    # Changing bounds of k_tp to avoid BoundError
    # Value are the just as closest posible to default values
    # pylinac.calibration.trs398.MAX_PTP = 1.2
    pylinac.calibration.trs398.MAX_PTP = max_PTP

    # from rawMeasurement_list_tries to measurement_list_tries
    # Convert the units and calculate the corrected charge and the temperature-pressure correction factor
    measurement_list_tries = list()

    for rawMeasurement_list in rawMeasurement_list_tries:
        measurement_list = list()
        for rawMeasurement in rawMeasurement_list:
            measurement = nel_calc.nel_aux.ConvertMeasurement(rawMeasurement=rawMeasurement, oldUnits=old_input_units, newUnits=new_input_units) #Conversion of units
            measurement["k_TP"] = pylinac.calibration.trs398.k_tp(temp = measurement["T"], press = measurement["P"])
            measurement["m_corrected"] = pylinac.calibration.trs398.m_corrected(m_reference=measurement["m"],
                                                            k_tp=measurement["k_TP"],
                                                            k_elec=1,
                                                            k_pol=1,
                                                            k_s=1)
            measurement_list.append(measurement.copy())
        measurement_list_tries.append(measurement_list.copy())

    # Calculate the average, standard deviation and expected value of m_corrected
    # from measurement_list_tries to m_corrected_average, m_corrected_stdDev and m_corrected_expectedValue
    m_corrected_averageList = list()
    m_corrected_stdDevList = list()
    m_corrected_expectedValueList = list()

    for measurement_list in measurement_list_tries:
        m_corrected_list = [measurement["m_corrected"] for measurement in measurement_list]

        # Calculate the average of m_corrected
        m_corrected_average_item = nel_calc.nel_aux.FindAverage(m_corrected_list)
        m_corrected_averageList.append(m_corrected_average_item)

        # Calculate the standard deviation of m_corrected
        m_corrected_stdDev_item = nel_calc.nel_aux.FindStdDev(m_corrected_list)
        m_corrected_stdDevList.append(m_corrected_stdDev_item)

        # Calculate the expected value of m_corrected
        m_corrected_expectedValue_item = nel_calc.nel_aux.FindExpectedValue(m_corrected_list)
        m_corrected_expectedValueList.append(m_corrected_expectedValue_item)

    m_corrected_average = nel_calc.nel_aux.FindAverage(m_corrected_averageList)
    m_corrected_stdDev = nel_calc.nel_aux.FindAverage(m_corrected_stdDevList)
    m_corrected_expectedValue = nel_calc.nel_aux.FindAverage(m_corrected_expectedValueList)
    
    print("General statistical quantities (Measurements 1, 2, 3):")
    print(f"Average: {m_corrected_average: .3f}")
    print(f"Standard deviation: {m_corrected_stdDev: .3f}")
    print(f"Expected value: {m_corrected_expectedValue: .3f}")

    # Creates output files.
    # .csv
    i = 0
    for i in range(len(measurement_list_tries)):
        filePath = filenames[i]
        dirs = pathlib.Path(filePath).parent
        stem = pathlib.Path(filePath).stem
        suffix = pathlib.Path(filePath).suffix
        #dirs, fileName = os.path.split(filePath)
        #baseName, extension = os.path.splitext(fileName)
        #output_extension = configJSON["files"]["output_preliminary"]["extension"]
        output_filename = f"{output_preffix}{stem}{suffix}"
        output_filePath = pathlib.Path(output_dir) / output_filename
        
        with open(output_filePath, "w", encoding="utf-8", newline='') as csvFile:
            csvWriter = csv.DictWriter(csvFile, fieldnames=output_header)
            csvWriter.writeheader()
            csvWriter.writerow(old_output_units)
            for measurement in measurement_list:
                csvWriter.writerow(measurement)
            print(f"Output file {output_filename} created.")
            i = i + 1

    # Create the summary file.
    # .json
    output_quantities = dict()
    output_quantities["m_corrected_average"] = m_corrected_average
    output_quantities["m_corrected_stdDev"] = m_corrected_stdDev
    output_quantities["m_corrected_expectedValue"] = m_corrected_expectedValue
    summaryPath = pathlib.Path(output_dir) / summary
    with open(summaryPath, "w", encoding="utf-8") as summaryFile:
        json.dump(output_quantities, summaryFile, indent=4)
        print(f"Output file {summary} created.")

    click.echo("Preliminary analysis done.")
    sys.exit(0)

@click.command()
@click.argument("filename", type=click.Path(file_okay=True, dir_okay=False), required=True)
@click.option("--protocol", type=click.STRING, callback=validate_config_path_exclusive_option, help="Protocol used for calculations.")
@click.option("--output", type=click.Path(file_okay=True, dir_okay=False), callback=validate_config_path_exclusive_option, help="Output analysis filename.")
@click.option("--config", type=click.Path(exists=True, file_okay=True), callback=validate_config_path_exclusive_option, help="Config filename.")
def analyze_image_planar(filename, protocol, output, config):
    """Analyze field images."""

    if config:
        # Load the config file.
        with open(config, "r", encoding = "utf-8") as configFile:
            configJSON = json.load(configFile)

        # Output filename.
        output = f"{configJSON["files"]["output-image-analysis"]["preffix"]}.{configJSON["files"]["output-image-analysis"]["extension"]}"

        protocol = None
        for configJSON_device in configJSON["devices"]:
            if configJSON["devices"][configJSON_device]["type"] == "epid":
                deviceStatus = configJSON["devices"][configJSON_device]["status"]
                if "default" in deviceStatus:
                    protocol = configJSON["devices"][configJSON_device]["protocol"]
                    break

    else:
        #Check if all the parameters are provided.
        if protocol is None or output is None:
            raise click.BadParameter("All parameters are required.")

    # Load input files: field images
    field_analysis = pylinac.FieldAnalysis(path=filename)
    
    # Picking the asked protocol.
    if protocol == "elekta":
        protocol_class = pylinac.Protocol.ELEKTA
    elif protocol == "varian":
        protocol_class = pylinac.Protocol.VARIAN
    elif protocol == "siemens":
        protocol_class = pylinac.Protocol.SIEMENS
    elif protocol == None:
        protocol_class = None
    else:
        raise ValueError(f"Unknown protocol: {protocol}.")
    
    # performing analysis
    field_analysis.analyze(protocol=protocol_class)
    field_analysis.plot_analyzed_image()
    field_analysis.publish_pdf(filename=output)
    
    click.echo(f"2D images analyzed.")
    sys.exit(0)

@click.command()
@click.argument("filename", type=click.Path(file_okay=True, dir_okay=False), required=True)
@click.option("--output", type=click.Path(file_okay=True, dir_okay=False), help="Output filename.")
@click.option("--config", type=click.Path(exists=True, file_okay=True), help="Config filename.")
def generate_calibration_report(filename, output, config):
    """Generate report about calibration."""

    # Load the config file.
    with open(config, "r", encoding = "utf-8") as configFile:
        configJSON = json.load(configFile)
    
    # Load the input file.
    with open(filename, "r", encoding = "utf-8") as inputFile:
        inputJSON = json.load(inputFile)
        
    trs398_calculator = pylinac.calibration.trs398.TRS398Photon(
        chamber=inputJSON["chamber"],
        clinical_pdd_zref=inputJSON["clinical_pdd_zref"],
        energy=inputJSON["energy"],
        fff=inputJSON["fff"],
        institution=inputJSON["institution"],
        k_elec=inputJSON["k_elec"],
        m_opposite=inputJSON["m_opposite"],
        m_reference=inputJSON["m_reference"],
        m_reduced=inputJSON["m_reduced"],
        measurement_date=inputJSON["measurement_date"],
        mu=inputJSON["mu"],
        n_dw=inputJSON["n_dw"],
        physicist=inputJSON["physicist"],
        press=inputJSON["press"],
        setup=inputJSON["setup"],
        temp=inputJSON["temp"],
        tissue_correction=inputJSON["tissue_correction"],
        tpr2010=inputJSON["tpr2010"],
        unit=inputJSON["unit"],
        voltage_reduced=inputJSON["voltage_reduced"],
        voltage_reference=inputJSON["voltage_reference"]
    )

    trs398_calculator.publish_pdf(
        filename=output,
        notes=inputJSON["notes"],
        open_file=False
        )
    click.echo(f"Output file {output} created.")
    sys.exit(0)

@click.command()
@click.argument('csv_file', type=click.Path(exists=True))
@click.option('--output', help='Filename to save the graph', required=True)
@click.option('--config', type=click.Path(exists=True, file_okay=True), help='Config filename.', required=True)
def generate_graph(csv_file, output, config):
    """Generates a graph from a given CSV file."""
    
    # Load the config file.
    with open(config, "r", encoding="utf-8") as configFile:
        configJSON = json.load(configFile)

    # Load data
    df = pd.read_csv(csv_file)

    # Assuming the first column is X and the second is Y
    plt.figure(figsize=(configJSON["pdd_graph"]["figsize"]["x"], configJSON["pdd_graph"]["figsize"]["y"]))
    plt.plot(df.iloc[:, 0], df.iloc[:, 1], marker='o', linestyle='-')
    
    # Customizing the plot
    plt.xlabel(configJSON["pdd_graph"]["xlabel"])
    plt.ylabel(configJSON["pdd_graph"]["ylabel"])
    plt.title(configJSON["pdd_graph"]["title"])
    plt.grid(configJSON["pdd_graph"]["grid"])

    # Save the graph
    plt.savefig(output)
    click.echo(f"Graph saved as {output}")
    sys.exit(0)

cli.add_command(create_config)
cli.add_command(create_image_planar)
cli.add_command(create_calibration)
cli.add_command(analyze_preliminary)
cli.add_command(analyze_image_planar)
cli.add_command(generate_calibration_report)
cli.add_command(generate_graph)

if __name__ == "__main__":
    cli()
    print(f"Program terminated.")