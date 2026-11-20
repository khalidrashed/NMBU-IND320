
# INN354 case project 2025H: R script for importing the raw event log data

# Load libraries
library(bupaverse)
library(dplyr)
library(tidyverse)

# Import raw data from CSV
# NOTE: Replace the path in the setwd command with your own. Windows users: remember to replace all backslashes (\) in the path with slashes (/)
setwd("C:/Users/joach/OneDrive - Norwegian University of Life Sciences/Teaching/INN354 - Systems and process innovation/Case project/2025")
raw_data <- read.csv("INN354 2025H Event log.csv")

# Change time stamp format from character (example: 2020-07-14T17:36:34Z) to POSIXct
raw_data$timestamp <- as.POSIXct(strptime(raw_data$timestamp, "%Y-%m-%dT%H:%M:%SZ"))
raw_data$invoice_date <- as.POSIXct(strptime(raw_data$invoice_date, "%Y-%m-%dT%H:%M:%SZ"))
raw_data$scan_date <- as.POSIXct(strptime(raw_data$scan_date, "%Y-%m-%dT%H:%M:%SZ"))

# Change variable type of invoice_id from integer to factor (otherwise the dotted charts will not work)
raw_data$invoice_id <- as.factor(raw_data$invoice_id)

# Create basic event log 
evlog <- eventlog(raw_data, 
                  case_id = "invoice_id",
                  activity_id = "activity_id", 
                  activity_instance_id = "event_id",
                  resource_id = "user_id",
                  timestamp = "timestamp", 
                  lifecycle_id = "lifecycle_id")

# Calculate some basic features of each case - very useful for further analysis (you may want to add more features of your own)
evlog %>% 
  group_by_case() %>% 
  summarise(
    n_events = n(), 
    n_users = n_distinct(user_id),
    invoice_date = first(invoice_date),
    start_date = min(timestamp),
    end_date = max(timestamp),
    end_event = last(activity_id),
    throughput_time_days = as.numeric(difftime(max(timestamp), min(timestamp), units = "days")),
    days_from_invoice_date_to_end = as.numeric(difftime(max(timestamp), min(invoice_date), units = "days")),
    first_approver = first(first_approver_id),
    second_approver = first(second_approver_id),
    spend_area = first(gl_account),
    vendor = first(vendor_id),
    cost_center = first(cost_center_id),
    profit_center = first(profit_center_id),
    invoice_amount = first(invoice_amount),
    currency = first(currency_id),
    n_approvals = sum(activity_id == "Approved")
  ) %>%
  arrange(invoice_id, start_date) ->
  case_stats

# Write the case statistics to a CSV file for further analysis in other software
write.csv(case_stats, file = "INN354 2025H Case statistics.csv")

