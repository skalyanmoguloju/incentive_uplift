# Development Log

## Day 1 — Development Environment Setup

### 1. Project Objective

Explain that the project will estimate the incremental effect of customer incentives on conversion. Mention that the project uses uplift modeling rather than only predicting whether a customer will convert.

### 2. Project Directory

Explain why the project uses separate folders for:

- Raw data
- Processed data
- Jupyter notebooks
- Source code
- Saved models
- Figures
- Reports

### 3. Python Environment

Record:

- Python version
- Operating system
- Why Python was selected
- Why a virtual environment was created
- The location of the project

Explain that the virtual environment isolates this project’s dependencies from other Python projects.

### 4. Installed Libraries

For every library, explain its purpose:

- Pandas for loading and manipulating tables
- NumPy for numerical arrays and calculations
- Scikit-learn for preprocessing, splitting data, and baseline models
- LightGBM for a tree-based baseline
- PyTorch for the multi-tower neural network
- Matplotlib and Seaborn for visualization
- Jupyter for interactive experimentation

### 5. Hardware Acceleration

Record:

- PyTorch version
- MPS availability
- Why MPS is useful
- Whether training will use Apple GPU acceleration or CPU fallback

Explain that MPS allows PyTorch to use Apple Silicon GPU hardware through Metal Performance Shaders.

### 6. Installation Problem

Describe the LightGBM error in your own words:

- LightGBM was installed successfully.
- It could not start because macOS could not find `libomp.dylib`.
- `libomp` provides the OpenMP runtime required for CPU parallelism.
- Homebrew was used to install the missing dependency.
- The import test succeeded afterward.

### 7. Verification

Record the final verification result:

- All core libraries imported successfully.
- PyTorch loaded successfully.
- MPS was available.
- The environment is ready for data processing and model development.

### 8. Day 1 Conclusion

Explain that the environment setup is complete and that the next step is downloading and inspecting the Starbucks dataset.




## Day 2 — Dataset Download and Inspection 


### Initial Dataset Sizes
portfolio.json: 10 rows, 6 columns
profile.json: 17,000 rows, 5 columns
transcript.json: 306,534 rows, 4 columns

### Dataset columns
portfolio
This describes the available incentives:
- reward: reward amount
- channels: delivery channels, such as web, email, mobile, or social
- difficulty: minimum spending requirement
- duration: offer-validity period in days
- offer_type: BOGO, discount, or informational
- id: unique offer identifier
profile
This describes each customer:
- gender: customer gender
- age: customer age
- id: unique customer identifier
- became_member_on: membership date stored as a number
- income: estimated customer income
transcript
This records customer events:
- person: customer identifier
- event: event type
- value: event-specific information
- time: hours since the beginning of the experiment


### Missing values
The portfolio dataset contains no missing values. All offer attributes,
including reward, channels, difficulty, duration, offer type, and offer ID,
are complete.

### Offer distribution
The transcript contains 306,534 chronological events. Transactions are the
largest event category, followed by offer receipts, offer views, and offer
completions. These events will later be used to reconstruct customer-offer
trajectories and define treatment and conversion outcomes.


The portfolio contains ten offers: four BOGO offers, four discount offers,
and two informational offers. The treatment variable will later be based on
these offer categories.

### Channel distribution
Email is available for all ten offers, mobile for nine, web for eight, and
social for six. Because offers can use multiple channels, these channel
counts are not mutually exclusive.

### Customer numerical summary
17,000 total customers - 2,175 missing = 14,825 available incomes




## Day 3 — Customer Event Timeline

### Time representation
- Transcript events are measured in hours from the beginning of the experiment.
- The time range is 0 to 714 hours.
- This corresponds to approximately 29.75 days, representing a 30-day experiment.
- A derived `time_days` column was created by dividing `time` by 24.

### Event structure
- Each transcript row represents one customer event.
- `person` identifies the customer.
- `event` identifies what happened.
- `value` contains event-specific information.
- `time` determines the chronological order.

### Event meanings
- `offer received`: an offer was delivered.
- `offer viewed`: the customer viewed the offer.
- `offer completed`: the offer requirement was completed.
- `transaction`: the customer made a purchase.

### Timeline observation
- A customer can receive and view an offer before making a transaction.
- A transaction and offer completion can occur at the same time.
- A customer can receive multiple offers during the experiment.
- Transactions do not directly contain an offer ID, so connecting a transaction to an offer requires time-window logic.

### Important modeling implication
- Events must be sorted by customer and time.
- Treatment must be determined before the conversion outcome.
- Post-treatment events must not be used as input features.
- A single customer timeline cannot prove causality; it only shows observed behavior.