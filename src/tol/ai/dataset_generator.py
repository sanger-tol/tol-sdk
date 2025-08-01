# SPDX-FileCopyrightText: 2025 Genome Research Ltd.
#
# SPDX-License-Identifier: MIT

import csv
import json
import random
from datasets import load_dataset


class DatasetGenerator():
    def __init__(self, data):
        self.data = data
        
    def __get_dataset(self):
        dataset = load_dataset('csv', data_files='src/tol/ai/attribute_data.csv')
        dataset = dataset.remove_columns(['id', 'authoritative', 'available_on_relationships','description', 'Keep/Remove', 'Reason', 'Comment'])
        dataset = dataset.filter(lambda x: x['display_name'] is not None)
        return dataset['train']

    def generate_training_data(self):
        """Generate more training examples for JSON generation"""
        
        dataset = self.__get_dataset()
        
        # Available attributes from your domain
        attributes = dataset['name']
        display_names = dataset['display_name']
        
        # Template phrases for input
        input_templates = [
            "generate a board that has a table showing {}",
            "make a board with a table including {}",
            "create a board with a table that displays {}",
            "build a board with a table containing {}",
            "show me a board with a table that includes {}",
            "create a dashboard with a table showing {}",
            "make a dashboard that displays {}",
            "generate a table with {}",
            "create a table showing {}",
            "build a table that contains {}"
        ]
        
        data = []
        
        for i in range(500):
            # Randomly select 1-4 attributes
            num_attrs = random.randint(1, 4)
            selected_indices = random.sample(range(len(display_names)), num_attrs)
            selected_display_names = [display_names[i] for i in selected_indices]
            selected_names = [attributes[i] for i in selected_indices]

            # Create natural language description
            if len(selected_display_names) == 1:
                attr_text = selected_display_names[0]
            elif len(selected_display_names) == 2:
                attr_text = f"{selected_display_names[0]} and {selected_display_names[1]}"
            else:
                attr_text = ", ".join(selected_display_names[:-1]) + f", and {selected_display_names[-1]}"

            # Generate input text
            template = random.choice(input_templates)
            input_text = template.format(attr_text)

            # Generate target JSON
            target_json = {
                "table": {
                    "title": "random",
                    "attributes": selected_names
                }
            }
            
            data.append({
                "input_text": input_text,
                "target_text": json.dumps(target_json)
            })
        
        # Write to CSV
        with open('src/tol/ai/expanded_training_data.csv', 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['input_text', 'target_text']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in data:
                writer.writerow(row)
        
        print(f"Generated 500 training examples in expanded_training_data.csv")
