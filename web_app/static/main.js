function range(start, end, step = 1) {
    const result = [];
    for (let i = start; i < end; i += step) {
        result.push(i);
    }
    return result;
}

function print_array(arr) {
    for (let i = 0; i < arr.length; i++)
        console.log(arr[i])
}

async function get_data(size) {
    const response = await fetch(`/api/get_data?size=${size}`);
    const data = await response.json();
    return data;
}

class DataHandler {
    constructor() {
        this.leftButton = document.getElementById('left_button_id');
        this.rightButton = document.getElementById('right_button_id');
        this.container = document.getElementById('container_id');
        this.audio = document.getElementById('audio_id');
        this.repeat = document.getElementById('repeat_id');
        this.text = document.getElementById('text_id');
        this.data_batch_size = 20;
        this.data_rest_minimum = 10;
        this.updating_is_running = false;
        this.items_are_modifying = false;
        this.start_is_clicked = false;
        // Attach click event handlers to the buttons
        this.leftButton.addEventListener('click', this.handleLeftButtonClick.bind(this));
        this.rightButton.addEventListener('click', this.handleRightButtonClick.bind(this));
        this.repeat.addEventListener('click', this.handleRepeatClick.bind(this));
        this.text.addEventListener('click', this.handleTextClick.bind(this));
    }
        // Load data when the page is loaded
    async start() {
        // const loadingAnimation = this.addLoadingAnimation();
        try {
          await this.updateItems(true);
          if (this.items.length > 0) {
                this.counter = 0;
                this.rest_counter = this.items.length - this.counter - 1
                this.removeLoadingAnimation();
                this.updateInfo(true);
            }
            
        } catch (error) {
            console.error('Error loading data:', error);
        }
    }

    addLoadingAnimation() {
        const loadingAnimation = document.createElement('div');
        loadingAnimation.className = 'loading-animation';
        this.container.appendChild(loadingAnimation);
        return loadingAnimation;
    }

    removeLoadingAnimation() {
        document.querySelector('.loading-overlay').style.display = 'none';
    }

    async updateItems(initLaunch) {
        if (this.updating_is_running == true) {
            return
        }
        if (this.rest_counter >= this.data_rest_minimum) {
            return
        }
        this.updating_is_running = true
        console.log('start updating items')
        if (initLaunch == true) {            
            this.items = await get_data(this.data_batch_size);
        } else {            
            const data_part = await get_data(this.data_batch_size);
            this.items_are_modifying = true;
            let passed_items = this.items.splice(0, this.counter)
            this.items = this.items.concat(data_part);
            this.counter = 0;
            this.rest_counter = this.items.length - this.counter - 1
            this.items_are_modifying = false;
            this.sendLogs(passed_items);
        }
        this.updating_is_running = false
        console.log('finish updating items', this.items.length, ' items')
    }
        
    handleLeftButtonClick() {
        this.handleButton('left');
    }

    handleRightButtonClick() {
        this.handleButton('right');
    }

    handleRepeatClick() {
        if (this.start_is_clicked == false) {
            this.repeat.textContent = 'repeat';
            this.start_is_clicked = true;
        }
        this.audio.play();
    }

    handleTextClick() {
        
        if (this.start_is_clicked == false)
            return
        
        if (this.word_is_shown == true)
            return;
        this.text.textContent = this.items[this.counter].word;
        this.word_is_shown = true;
    }

    refreshText() {
        this.word_is_shown = false;
        this.text.textContent = 'show'
    }
    
    _print_info() {
        // console.log(this.word_is_shown)
        // console.log('counter - ', this.counter, ', rest counter - ', this.rest_counter)
        // console.log('len if items - ', this.items.length)
        // print_array(this.items);
    }

    updateInfo() {
        const item = this.items[this.counter];
        this.audio.src = item.signed_url;
        this.audio.play();
        this.refreshText();
    }
    
    handleButton(direction) {

        if (this.start_is_clicked == false)
            return

        if (this.items_are_modifying == true) {
            this._print_info()
            return
        }
        
        if (this.rest_counter == 0) {
            this._print_info()
            return
        }
        this.items[this.counter].button = direction;
        this.counter ++;
        this.rest_counter --;
        this.updateInfo();   
        
        if (this.rest_counter < this.data_rest_minimum) {
            if (this.updating_is_running == false) {
                this.updateItems(false);
            }
        }
        this._print_info()
    }

    sendLogs(items) {
    		console.log('send data');
        return;
        try {
            const response = fetch('/api/process_logs', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.items),
            });

            if (response.ok) {
                console.log('Data sent successfully.');
            } else {
                console.error('Error sending data to the server.');
            }
        } catch (error) {
            console.error('Error sending data:', error);
        }
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    // Your code here
    const dh = new DataHandler();
    await dh.start();
});
// async function main() {
//     const data = await get_data(10);
//     console.log(data);
// }

// main();

