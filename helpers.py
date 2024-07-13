import requests
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
import os
import json
import config


def update_config_file(updates):
    lines = []
    with open(config.CONFIG_FILE_PATH, 'r') as file:
        lines = file.readlines()

    with open(config.CONFIG_FILE_PATH, 'w') as file:
        for line in lines:
            for key, value in updates.items():
                if line.startswith(f"{key} ="):
                    if isinstance(value, str):
                        file.write(f"{key} = '{value}'\n")
                    else:
                        file.write(f"{key} = {value}\n")
                    break
            else:
                file.write(line)


def register():
    try:
        url = config.productCatalogURL + config.registrationEndpoint

        params = {
            "service_name": config.serviceName
        }

        response = requests.get(url=url, params=params)
        status_code = response.status_code

        if status_code == 200:
            response_data = response.json()

            updates = {
                'messageBrokerIP': response_data.get('messageBrokerIP', config.messageBrokerIP),
                'messageBrokerPort': response_data.get('messageBrokerPort', config.messageBrokerPort),
                'registerInterval': response_data.get('registerInterval', config.registerInterval),
                'ip': response_data.get('ip', config.ip),
                'port': response_data.get('port', config.port),
                'productCatalogURL': response_data.get('productCatalogURL', config.productCatalogURL),
                'registrationEndpoint': response_data.get('registrationEndpoint', config.registrationEndpoint),
                'statisticsCalculatorIP': response_data.get('statisticsCalculatorIP', config.statisticsCalculatorIP),
                'status': response_data.get('status', config.status)
            }

            update_config_file(updates)

            print("Configuration saved.")
            return "Configuration saved.", 200

        else:
            print(f"Failed to retrieve data: Status code {status_code}")
            return f"Failed to retrieve data: Status code {status_code}", status_code

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return f"Request error: {e}", 500

    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return f"JSON decode error: {e}", 500

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return f"An unexpected error occurred: {e}", 500


def fetch_sensor_data(url):
    response = requests.get(url)
    data = response.json()
    return data


def plot_sensor_data(sensor_name, times, values):
    plt.figure(figsize=(10, 5))
    plt.plot(times, values, marker='o')
    plt.title(f'{sensor_name.capitalize()} Sensor Data')
    plt.xlabel('Time')
    plt.ylabel(f'{sensor_name.capitalize()} Value')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plot_filename = f'{sensor_name}_plot.png'
    plt.savefig(plot_filename)
    plt.close()
    return plot_filename


def delete_old_pdf(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as e:
        print(f"Error: {file_path} : {e.strerror}")


def generate_pdf_report(sensor_data):
    pdf_output_filename = 'climate_watch_report.pdf'

    # Delete old PDF file
    delete_old_pdf(pdf_output_filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Sensor Data Report", ln=True, align='C')

    for sensor_name, data in sensor_data.items():
        times = [datetime.fromisoformat(item['time'].replace('Z', '')).strftime('%Y-%m-%d %H:%M:%S') for item in
                 data['data']]
        values = [item['value'] for item in data['data']]

        plot_filename = plot_sensor_data(sensor_name, times, values)

        # Add sensor data and statistics to the PDF
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=16)
        pdf.cell(200, 10, txt=f'{sensor_name.capitalize()} Sensor Data', ln=True, align='L')
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt=f'Mean: {data["mean"]}', ln=True, align='L')
        pdf.cell(200, 10, txt=f'Median: {data["median"]}', ln=True, align='L')
        pdf.cell(200, 10, txt=f'Mode: {data["mode"]}', ln=True, align='L')
        pdf.cell(200, 10, txt=f'Min: {data["min"]}', ln=True, align='L')
        pdf.cell(200, 10, txt=f'Max: {data["max"]}', ln=True, align='L')
        pdf.cell(200, 10, txt=f'Range: {data["range"]}', ln=True, align='L')
        pdf.cell(200, 10, txt=f'Variance: {data["variance"]}', ln=True, align='L')
        pdf.cell(200, 10, txt=f'Standard Deviation: {data["standard_deviation"]}', ln=True, align='L')
        pdf.image(plot_filename, x=10, y=pdf.get_y() + 10, w=180)

        # Add data table to the PDF
        pdf.add_page()
        pdf.set_font("Arial", 'B', size=12)
        pdf.cell(200, 10, txt='Data Table', ln=True, align='L')
        pdf.set_font("Arial", size=10)

        pdf.cell(90, 10, txt='Date', border=1, align='C')
        pdf.cell(90, 10, txt=f'{sensor_name.capitalize()} Value', border=1, ln=True, align='C')

        for time, value in zip(times, values):
            pdf.cell(90, 10, txt=time, border=1)
            pdf.cell(90, 10, txt=str(value), border=1, ln=True)

        os.remove(plot_filename)

    pdf.output(pdf_output_filename)
    return os.path.abspath(pdf_output_filename)


def prepareration_process(place_id):
    api_urls = {
        'temperature': f'{config.statisticsCalculatorIP}?sensor_name=temperature&place_id={place_id}',
        'humidity': f'{config.statisticsCalculatorIP}?sensor_name=humidity&place_id={place_id}',
        'smoke': f'{config.statisticsCalculatorIP}?sensor_name=smoke&place_id={place_id}'
    }

    sensor_data = {}
    for key, url in api_urls.items():
        data = fetch_sensor_data(url)
        if data:
            sensor_data[key] = data

    if sensor_data:
        pdf_filename = generate_pdf_report(sensor_data)
        return pdf_filename
    else:
        print("No sensor data available to generate the report.")
        return None
