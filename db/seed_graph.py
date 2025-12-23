"""
Seed Neo4j Aura database with synthetic data.

Usage: python seed_graph.py

Environment variables required:
- NEO4J_URI: Neo4j Aura connection URI
- NEO4J_USER: Database username (usually 'neo4j')
- NEO4J_PASSWORD: Database password
"""

import os
import random
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables from .env file
load_dotenv()


class Neo4jSeeder:
    def __init__(self, uri, username, password):
        # Initialize Neo4j driver - SSL is auto-configured with neo4j+s:// URI
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
    
    def close(self):
        self.driver.close()
    
    def clear_database(self):
        """Clear all nodes and relationships from the database."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("✓ Database cleared")
    
    def create_companies(self):
        """Create 5 company nodes."""
        companies = [
            {"name": "TechCorp Solutions", "industry": "Technology"},
            {"name": "HealthFirst Medical", "industry": "Healthcare"},
            {"name": "GreenEnergy Systems", "industry": "Energy"},
            {"name": "FinanceHub Inc", "industry": "Finance"},
            {"name": "RetailGiant Co", "industry": "Retail"}
        ]
        
        with self.driver.session() as session:
            for company in companies:
                session.run(
                    "MERGE (c:Company {name: $name}) "
                    "SET c.industry = $industry",
                    name=company["name"],
                    industry=company["industry"]
                )
            print(f"✓ Created {len(companies)} companies")
        
        return [c["name"] for c in companies]
    
    def create_products(self):
        """Create 10 product nodes."""
        products = [
            {"name": "CloudSync Pro", "category": "Software"},
            {"name": "DataAnalyzer X", "category": "Analytics"},
            {"name": "SecureVault", "category": "Security"},
            {"name": "TeamChat Plus", "category": "Communication"},
            {"name": "ProjectFlow", "category": "Project Management"},
            {"name": "InvoiceMaster", "category": "Finance"},
            {"name": "InventoryTrack", "category": "Operations"},
            {"name": "CustomerCRM", "category": "Sales"},
            {"name": "HRConnect", "category": "Human Resources"},
            {"name": "MarketingHub", "category": "Marketing"}
        ]
        
        with self.driver.session() as session:
            for product in products:
                session.run(
                    "MERGE (p:Product {name: $name}) "
                    "SET p.category = $category",
                    name=product["name"],
                    category=product["category"]
                )
            print(f"✓ Created {len(products)} products")
        
        return [p["name"] for p in products]
    
    def create_people(self, company_names):
        """Create 50 person nodes and assign them to companies."""
        first_names = [
            "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
            "Isabella", "William", "Mia", "James", "Charlotte", "Benjamin", "Amelia",
            "Lucas", "Harper", "Henry", "Evelyn", "Alexander", "Abigail", "Michael",
            "Emily", "Daniel", "Elizabeth", "Matthew", "Sofia", "Jackson", "Avery",
            "David", "Ella", "Joseph", "Scarlett", "Samuel", "Grace", "Sebastian",
            "Chloe", "John", "Victoria", "Andrew", "Riley", "Joshua", "Aria",
            "Christopher", "Lily", "Anthony", "Aubrey", "Dylan", "Zoey", "Thomas"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
            "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
            "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
            "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
            "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
            "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
            "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
            "Carter", "Roberts"
        ]
        
        roles = [
            "Software Engineer", "Senior Software Engineer", "Engineering Manager",
            "Product Manager", "Data Analyst", "Data Scientist", "UX Designer",
            "DevOps Engineer", "QA Engineer", "Marketing Manager", "Sales Manager",
            "Account Executive", "Customer Success Manager", "HR Manager",
            "Finance Analyst", "Operations Manager", "CEO", "CTO", "CFO", "VP Engineering"
        ]
        
        people = []
        with self.driver.session() as session:
            for i in range(50):
                name = f"{random.choice(first_names)} {random.choice(last_names)}"
                role = random.choice(roles)
                company = random.choice(company_names)
                
                session.run(
                    "MERGE (p:Person {name: $name}) "
                    "SET p.role = $role",
                    name=name,
                    role=role
                )
                
                # Create WORKS_AT relationship
                session.run(
                    "MATCH (p:Person {name: $person_name}) "
                    "MATCH (c:Company {name: $company_name}) "
                    "MERGE (p)-[:WORKS_AT]->(c)",
                    person_name=name,
                    company_name=company
                )
                
                people.append({"name": name, "role": role, "company": company})
            
            print(f"✓ Created {len(people)} people")
            print(f"✓ Created WORKS_AT relationships")
        
        return [p["name"] for p in people]
    
    def create_company_product_relationships(self, company_names, product_names):
        """Create USES relationships between companies and products."""
        with self.driver.session() as session:
            relationships = 0
            for company in company_names:
                # Each company uses 3-6 random products
                num_products = random.randint(3, 6)
                selected_products = random.sample(product_names, num_products)
                
                for product in selected_products:
                    session.run(
                        "MATCH (c:Company {name: $company_name}) "
                        "MATCH (p:Product {name: $product_name}) "
                        "MERGE (c)-[:USES]->(p)",
                        company_name=company,
                        product_name=product
                    )
                    relationships += 1
            
            print(f"✓ Created {relationships} USES relationships")
    
    def create_reporting_relationships(self, person_names):
        """Create REPORTS_TO relationships between people."""
        with self.driver.session() as session:
            # Get people grouped by company
            result = session.run(
                "MATCH (p:Person)-[:WORKS_AT]->(c:Company) "
                "RETURN p.name as name, c.name as company"
            )
            
            company_people = {}
            for record in result:
                company = record["company"]
                if company not in company_people:
                    company_people[company] = []
                company_people[company].append(record["name"])
            
            relationships = 0
            # Within each company, create reporting relationships
            for company, people in company_people.items():
                if len(people) > 1:
                    # 30-50% of people report to someone
                    num_reports = random.randint(
                        int(len(people) * 0.3),
                        int(len(people) * 0.5)
                    )
                    
                    reporters = random.sample(people, min(num_reports, len(people)))
                    
                    for reporter in reporters:
                        # Choose a different person as manager
                        potential_managers = [p for p in people if p != reporter]
                        if potential_managers:
                            manager = random.choice(potential_managers)
                            
                            session.run(
                                "MATCH (reporter:Person {name: $reporter_name}) "
                                "MATCH (manager:Person {name: $manager_name}) "
                                "MERGE (reporter)-[:REPORTS_TO]->(manager)",
                                reporter_name=reporter,
                                manager_name=manager
                            )
                            relationships += 1
            
            print(f"✓ Created {relationships} REPORTS_TO relationships")
    
    def print_statistics(self):
        """Print database statistics."""
        with self.driver.session() as session:
            # Count nodes
            result = session.run(
                "MATCH (n) "
                "RETURN labels(n)[0] as label, count(*) as count "
                "ORDER BY label"
            )
            print("\n--- Database Statistics ---")
            print("Nodes:")
            for record in result:
                print(f"  {record['label']}: {record['count']}")
            
            # Count relationships
            result = session.run(
                "MATCH ()-[r]->() "
                "RETURN type(r) as type, count(*) as count "
                "ORDER BY type"
            )
            print("\nRelationships:")
            for record in result:
                print(f"  {record['type']}: {record['count']}")
    
    def seed(self):
        """Execute the complete seeding process."""
        print("Starting database seeding...")
        print("-" * 50)
        
        # Clear existing data
        self.clear_database()
        
        # Create nodes
        company_names = self.create_companies()
        product_names = self.create_products()
        person_names = self.create_people(company_names)
        
        # Create relationships
        self.create_company_product_relationships(company_names, product_names)
        self.create_reporting_relationships(person_names)
        
        # Print statistics
        self.print_statistics()
        
        print("-" * 50)
        print("✓ Database seeding completed successfully!")


def main():
    # Load environment variables
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not all([uri, username, password]):
        print("Error: Missing required environment variables")
        print("Please set: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        return
    
    # Create seeder and run
    seeder = Neo4jSeeder(uri, username, password)
    try:
        seeder.seed()
    finally:
        seeder.close()


if __name__ == "__main__":
    main()
