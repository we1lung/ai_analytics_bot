import csv
import random
from datetime import datetime, timedelta

def generate_company_data(filename, num_rows):
    headers = ['employee_id', 'full_name', 'department', 'position', 'salary', 'hire_date', 'performance_score']
    
    deps = {
        'IT': ['Backend Dev', 'Frontend Dev', 'QA Engineer', 'DevOps', 'Data Scientist'],
        'Sales': ['Account Manager', 'Sales Representative', 'Sales Lead'],
        'HR': ['Recruiter', 'HR Manager', 'Payroll Specialist'],
        'Marketing': ['SEO Specialist', 'Content Manager', 'SMM'],
        'Finance': ['Accountant', 'Financial Analyst', 'Auditor']
    }
    
    first_names = ['Liam', 'Noah', 'Oliver', 'James', 'Emma', 'Charlotte', 'Amelia', 'Sophia']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis']

    with open(filename, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for i in range(1, num_rows + 1):
            dept = random.choice(list(deps.keys()))
            pos = random.choice(deps[dept])
            
            # Генерация данных
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            salary = random.randint(40000, 150000)
            performance = round(random.uniform(1.0, 5.0), 1)
            
            # Дата найма за последние 10 лет
            days_ago = random.randint(0, 3650)
            hire_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')

            writer.writerow([i, name, dept, pos, salary, hire_date, performance])
            
            if i % 100000 == 0:
                print(f"Записано {i} сотрудников...")

if __name__ == "__main__":
    count = 1000  # Поставь 1 000 000 для реально большого файла
    generate_company_data('company_test_data.csv', count)
    print(f"Готово! Создан файл на {count} строк.")