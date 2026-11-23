# Input Schema

## 1. Structure of the model

Each row from the model represents one decision during a defined observation window.

A single example contains:

- Customer and historical-behavior features
- Features of the associated offer
- The treatment identifier
- The observed binary outcome

The treatment identifier indicates whether the customer received the control condition or one of the available offers.

## 2. Feature Tensors

The customer and historical-behavior features will be stored into `customer_features` tensor.

The offer-related features will be stored in `incentive_features` tensor.

We will use the same for the synthetic data validation and below are the expected shapes:
- `customer_features`: `(batch_size, 8)`
- `incentive_features`: `(batch_size, 6)`

The feature counts are temporary values for testing and will be updated after the final processing

## 3. Treatment Tensor

The treatment tensor will be named `treatment`.

Each value identifies the treatment assigned to one customer:

- `0` represents the control condition.
- `1` through `10` represent the ten available offers.