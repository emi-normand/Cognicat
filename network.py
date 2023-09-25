from flask import Flask, request
from uvicmuse.MuseWrapper import MuseWrapper as MW
import asyncio
import time
import threading
import csv

app = Flask(__name__)
loop = asyncio.get_event_loop()
muse = MW (loop = loop,
            timeout = 10,
            max_buff_len = 500,
            target_name= 'Muse-CA40') 
connected = muse.search_and_connect() # returns True if the connection is successful
print(f"connection: {connected}")

experiment_start_time = 0
remote_device_time = 0
current_event = 0
eeg_data = {
    'TP9': [],
    'AF7': [],
    'AF8': [],
    'TP10': [],
    'Ref': [],
    'Timestamp': [],
    'Image': [],
    'Image-Timestamp': [],
    'Remote-Time': []
}
stop_thread = threading.Event()  # Event to signal the termination of the thread
eeg_thread = None
file_name = None

@app.route('/start', methods=['POST'])
def start():
    global experiment_start_time, eeg_data, eeg_thread,stop_thread, file_name, current_event
    eeg_data = {
    'TP9': [],
    'AF7': [],
    'AF8': [],
    'TP10': [],
    'Ref': [],
    'Timestamp': [],
    'Image': [],
    'Image-Timestamp': [],
    'Remote-Time': []
}
    print('Received start command')
    experiment_start_time = time.time()
    file_name = experiment_start_time
    current_event = 0
    stop_thread = threading.Event() 
    # Start the EEG data acquisition thread
    eeg_thread = threading.Thread(target=pull_eeg_data, args=(stop_thread,))
    eeg_thread.daemon = True  # Set the thread as a daemon to automatically terminate when the main thread ends
    eeg_thread.start()
    return 'Start command received'

@app.route('/stop', methods=['POST'])
def stop():
    global experiment_start_time,stop_thread, eeg_thread, eeg_data, file_name
    experiment_start_time = 0
    stop_thread.set()  # Set the stop event to terminate the thread
    # Wait for the thread to complete before continuing
    print('Waiting for EEG thread to complete')
    if eeg_thread and eeg_thread.is_alive():
        # Wait for the thread to complete before continuing
        print('Waiting for EEG thread to complete')
        eeg_thread.join()
        print('EEG thread completed')
    else:
        print('EEG thread not running')

    # Save the EEG data to a file
    print('Saving EEG data to file')
    with open(f'{file_name}.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(['TP9','AF7','AF8','TP10','Ref','Timestamp','Image','Image-Timestamp','Remote-Time'])
        for i in range(len(eeg_data['TP9'])):
            writer.writerow([eeg_data['TP9'][i],eeg_data['AF7'][i], eeg_data['AF8'][i], eeg_data['TP10'][i], eeg_data['Ref'][i], eeg_data['Timestamp'][i], eeg_data['Image'][i], eeg_data['Image-Timestamp'][i], eeg_data['Remote-Time'][i]])
    
    print('EEG data saved to file')
    return 'stop command received'

@app.route('/update_event', methods=['POST'])
def update_event():
    global current_event, experiment_start_time, remote_device_time
    current_event = request.form.get('event_id')
    experiment_start_time = time.time()
    remote_device_time = request.form.get('timestamp')
    print(len(eeg_data['TP9']))
    
    print(f'Received new event {current_event} at {experiment_start_time}')
    return 'stop command received'

# Function to continuously pull data from the EEG device
def pull_eeg_data(stop_thread):
    # Replace this with your actual logic to pull data from the EEG device
    while True:
        # Simulating data retrieval from the EEG device
        data = muse.pull_eeg()
        for sample in data:
            eeg_data['TP9'].append(sample[0])
            eeg_data['AF7'].append(sample[1])
            eeg_data['AF8'].append(sample[2])
            eeg_data['TP10'].append(sample[3])
            eeg_data['Ref'].append(sample[4])
            eeg_data['Timestamp'].append(sample[5])
            eeg_data['Image'].append(current_card)
            eeg_data['Image-Timestamp'].append(experiment_start_time)
            eeg_data['Remote-Time'].append(remote_device_time)

        # Adjust the sleep duration based on your data acquisition rate
        time.sleep(0.05) 
        if stop_thread.is_set():
            break


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)