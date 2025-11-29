"""
Batch Plant Production Scheduling System
Combines Salabim simulation with optimization
"""

import salabim as sim
from dataclasses import dataclass, field
from typing import List, Dict, Tuple
from math import ceil
import json


# ============================================================================
# DATA STRUCTURES - Change these to modify the problem
# ============================================================================

@dataclass
class Equipment:
    """Equipment resource definition"""
    id: str
    type: str
    capacity: float  # L or kg
    
    def __repr__(self):
        return f"{self.id}({self.type}, {self.capacity})"


@dataclass
class RecipeStep:
    """Single step in a recipe"""
    step_name: str
    equipment_type: str
    duration: float  # hours
    
    def __repr__(self):
        return f"{self.step_name}[{self.equipment_type}, {self.duration}h]"


@dataclass
class Product:
    """Product with recipe"""
    id: str
    name: str
    recipe: List[RecipeStep]
    batch_size: float  # kg per batch
    
    def total_processing_time(self) -> float:
        return sum(step.duration for step in self.recipe)
    
    def __repr__(self):
        return f"{self.name}({self.batch_size}kg, {self.total_processing_time()}h)"


@dataclass
class Order:
    """Customer order"""
    id: str
    product_id: str
    quantity: float  # kg
    due_date: float  # days
    priority: int = 1  # 1=low, 2=medium, 3=high, 4=critical
    
    def __repr__(self):
        return f"Order-{self.id}({self.product_id}, {self.quantity}kg, due={self.due_date}d)"


@dataclass 
class ChangeoverMatrix:
    """Sequence-dependent changeover times"""
    matrix: Dict[Tuple[str, str], float]  # (from_product, to_product) -> hours
    
    def get_time(self, from_prod: str, to_prod: str) -> float:
        if from_prod == to_prod:
            return 0.0
        return self.matrix.get((from_prod, to_prod), 0.0)


# ============================================================================
# PROBLEM DATA - MODIFY THESE VALUES
# ============================================================================

class PlantData:
    """Centralized plant configuration - CHANGE VALUES HERE"""
    
    # Equipment configuration
    EQUIPMENT = [
        Equipment("R-101", "Reactor", 500),
        Equipment("R-102", "Reactor", 500),
        Equipment("D-201", "Dryer", 200),
        Equipment("P-301", "Packager", 100),
    ]
    
    # Product recipes
    PRODUCTS = [
        Product(
            "A", "Product-A",
            recipe=[
                RecipeStep("Reaction", "Reactor", 4.0),
                RecipeStep("Drying", "Dryer", 8.0),
                RecipeStep("Packaging", "Packager", 2.0),
            ],
            batch_size=100
        ),
        Product(
            "B", "Product-B", 
            recipe=[
                RecipeStep("Reaction", "Reactor", 6.0),
                RecipeStep("Drying", "Dryer", 6.0),
                RecipeStep("Packaging", "Packager", 1.5),
            ],
            batch_size=80
        ),
        Product(
            "C", "Product-C",
            recipe=[
                RecipeStep("Reaction", "Reactor", 3.0),
                RecipeStep("Drying", "Dryer", 10.0),
                RecipeStep("Packaging", "Packager", 2.5),
            ],
            batch_size=120
        ),
    ]
    
    # Changeover times (hours) between products
    CHANGEOVERS = ChangeoverMatrix({
        ("A", "B"): 4.0,
        ("A", "C"): 6.0,
        ("B", "A"): 5.0,
        ("B", "C"): 3.0,
        ("C", "A"): 8.0,
        ("C", "B"): 4.0,
    })
    
    # Orders - INCREASED DEMAND to stress the system
    ORDERS = [
        Order("1", "A", 1000, due_date=1, priority=2),   # Was 500
        Order("2", "B", 800, due_date=4, priority=2),   # Was 400
        Order("3", "C", 1200, due_date=5, priority=4),   # Was 600 - TIGHT!
        Order("4", "A", 600, due_date=3, priority=1),   # Was 300
        Order("5", "B", 500, due_date=2, priority=3),    # NEW
        Order("6", "C", 400, due_date=6, priority=2),    # NEW
    ]
    
    # Simulation parameters
    HOURS_PER_DAY = 24
    SIMULATION_TIME = 30 * HOURS_PER_DAY  # 30 days in hours


# ============================================================================
# SALABIM SIMULATION MODEL
# ============================================================================

class BatchProcess(sim.Component):
    """Simulates a single batch going through recipe steps"""
    
    def setup(self, batch_id, product, order, 
              equipment_resources, changeover_tracker, start_delay=0):
        self.batch_id = batch_id
        self.product = product
        self.order = order
        self.equipment_resources = equipment_resources
        self.changeover_tracker = changeover_tracker
        self.start_delay = start_delay
        self.start_time = None
        self.end_time = None
        self.batch_status = "created"  # Renamed from 'status'
        
    def process(self):
        """Execute recipe steps sequentially"""
        # Wait for scheduled start time
        if self.start_delay > 0:
            yield self.hold(self.start_delay)
        
        self.start_time = self.env.now()
        self.batch_status = "processing"
        
        for step_idx, step in enumerate(self.product.recipe):
            # Get resource pool for this equipment type
            resource_pool = self.equipment_resources[step.equipment_type]
            
            # Request one unit of equipment (will wait if all busy)
            yield self.request(resource_pool, priority=-self.order.priority)
            
            # Determine which specific equipment instance we got
            # (Salabim assigns from pool, we track by resource pool name)
            resource_key = f"{step.equipment_type}"
            
            # Check if changeover needed (only for first step on equipment)
            if step_idx == 0:  # Only changeover on first equipment usage
                last_product = self.changeover_tracker.get(resource_key)
                if last_product and last_product != self.product.id:
                    changeover_time = PlantData.CHANGEOVERS.get_time(last_product, self.product.id)
                    if changeover_time > 0:
                        yield self.hold(changeover_time)
                
                # Update tracker for next batch
                self.changeover_tracker[resource_key] = self.product.id
            
            # Execute processing step
            yield self.hold(step.duration)
            
            # Release equipment
            self.release(resource_pool)
        
        self.end_time = self.env.now()
        self.batch_status = "completed"


class ProductionScheduler:
    """Schedules and simulates batch production"""
    
    def __init__(self, plant_data: PlantData):
        self.data = plant_data
        self.env = None
        self.equipment_resources = {}
        self.changeover_tracker = {}
        self.batches = []
        
    def setup_simulation(self):
        """Initialize Salabim environment and resources"""
        # Set to yield mode (non-yieldless) BEFORE creating environment
        sim.yieldless(False)
        self.env = sim.Environment(trace=False)
        
        # Create resource pools for each equipment type
        equipment_by_type = {}
        for equip in self.data.EQUIPMENT:
            if equip.type not in equipment_by_type:
                equipment_by_type[equip.type] = []
            equipment_by_type[equip.type].append(equip)
        
        # Create Salabim resources (capacity = number of equipment of that type)
        self.equipment_resources = {}
        for equip_type, equip_list in equipment_by_type.items():
            self.equipment_resources[equip_type] = sim.Resource(
                name=equip_type,
                capacity=len(equip_list),
                env=self.env
            )
        
        self.changeover_tracker = {}
    
    def generate_batches_for_orders(self) -> List[Tuple[Order, Product, int]]:
        """
        Generate required batches for all orders
        Returns: List of (order, product, batch_number)
        """
        batches = []
        for order in self.data.ORDERS:
            product = next(p for p in self.data.PRODUCTS if p.id == order.product_id)
            batches_needed = ceil(order.quantity / product.batch_size)
            
            for batch_num in range(batches_needed):
                batches.append((order, product, batch_num))
        
        return batches
    
    def create_schedule_simple_fifo(self) -> List[Tuple[str, str, int, float]]:
        """
        Simple FIFO schedule: process orders in priority order
        Returns: List of (order_id, product_id, batch_num, start_time)
        """
        schedule = []
        
        # Generate all required batches
        all_batches = self.generate_batches_for_orders()
        
        # Sort by order priority (high first), then due date
        all_batches.sort(key=lambda x: (-x[0].priority, x[0].due_date))
        
        # Schedule all batches at time 0 (let simulation handle queueing)
        for order, product, batch_num in all_batches:
            schedule.append((order.id, product.id, batch_num, 0.0))
        
        return schedule
    
    def create_schedule_edd(self) -> List[Tuple[str, str, int, float]]:
        """
        Earliest Due Date (EDD) schedule: process orders by due date
        Returns: List of (order_id, product_id, batch_num, start_time)
        """
        schedule = []
        
        # Generate all required batches
        all_batches = self.generate_batches_for_orders()
        
        # Sort ONLY by due date (earliest first), ignore priority
        all_batches.sort(key=lambda x: x[0].due_date)
        
        # Schedule all batches at time 0 (let simulation handle queueing)
        for order, product, batch_num in all_batches:
            schedule.append((order.id, product.id, batch_num, 0.0))
        
        return schedule
    
    def create_schedule_cr(self) -> List[Tuple[str, str, int, float]]:
        """
        Critical Ratio schedule: priority = (due_date - now) / processing_time
        Returns: List of (order_id, product_id, batch_num, start_time)
        """
        schedule = []
        
        # Generate all required batches
        all_batches = self.generate_batches_for_orders()
        
        # Calculate critical ratio for each order
        # Lower ratio = more critical (less slack time per unit work)
        def critical_ratio(order, product):
            processing_time = product.total_processing_time() / self.data.HOURS_PER_DAY
            batches_needed = ceil(order.quantity / product.batch_size)
            total_time_needed = processing_time * batches_needed
            slack = order.due_date - total_time_needed
            return slack / total_time_needed if total_time_needed > 0 else 999
        
        all_batches.sort(key=lambda x: critical_ratio(x[0], x[1]))
        
        # Schedule all batches at time 0
        for order, product, batch_num in all_batches:
            schedule.append((order.id, product.id, batch_num, 0.0))
        
        return schedule
    
    def simulate_schedule(self, schedule: List[Tuple[str, str, int, float]]) -> Dict:
        """
        Simulate a given schedule
        schedule: List of (order_id, product_id, batch_num, start_time)
        Returns: Performance metrics
        """
        self.setup_simulation()
        self.batches = []
        
        # Create batch processes according to schedule
        for idx, (order_id, product_id, batch_num, start_time) in enumerate(schedule):
            order = next(o for o in self.data.ORDERS if o.id == order_id)
            product = next(p for p in self.data.PRODUCTS if p.id == product_id)
            
            batch = BatchProcess(
                batch_id=f"B{idx:03d}-O{order_id}-P{product_id}-{batch_num}",
                product=product,
                order=order,
                equipment_resources=self.equipment_resources,
                changeover_tracker=self.changeover_tracker,
                start_delay=start_time,
                env=self.env
            )
            self.batches.append(batch)
        
        # Run simulation
        self.env.run(till=self.data.SIMULATION_TIME)
        
        # Calculate metrics
        return self.calculate_metrics()
    
    def calculate_metrics(self) -> Dict:
        """Calculate performance metrics from simulation results"""
        metrics = {
            'makespan': 0.0,
            'total_tardiness': 0.0,
            'num_late_orders': 0,
            'utilization': {},
            'order_completion': {},
            'batch_details': []
        }
        
        # Collect batch completion times by order
        order_batch_completions = {}
        for batch in self.batches:
            if batch.end_time:
                order_id = batch.order.id
                if order_id not in order_batch_completions:
                    order_batch_completions[order_id] = []
                order_batch_completions[order_id].append(batch.end_time)
                
                metrics['batch_details'].append({
                    'batch_id': batch.batch_id,
                    'product': batch.product.id,
                    'start': batch.start_time / self.data.HOURS_PER_DAY,
                    'end': batch.end_time / self.data.HOURS_PER_DAY,
                    'duration': (batch.end_time - batch.start_time) / self.data.HOURS_PER_DAY
                })
        
        # Calculate per-order metrics
        for order in self.data.ORDERS:
            if order.id in order_batch_completions:
                # Order is complete when ALL its batches are done
                completion_time = max(order_batch_completions[order.id]) / self.data.HOURS_PER_DAY
                tardiness = max(0, completion_time - order.due_date)
                
                metrics['order_completion'][order.id] = {
                    'completion_day': completion_time,
                    'due_day': order.due_date,
                    'tardiness_days': tardiness,
                    'num_batches': len(order_batch_completions[order.id])
                }
                
                metrics['total_tardiness'] += tardiness
                if tardiness > 0:
                    metrics['num_late_orders'] += 1
                
                metrics['makespan'] = max(metrics['makespan'], completion_time)
        
        # Calculate equipment utilization
        for equip_type, resource in self.equipment_resources.items():
            if self.env.now() > 0:
                # Occupancy returns time-weighted utilization
                utilization = resource.occupancy.mean() * 100
                metrics['utilization'][equip_type] = f"{utilization:.1f}%"
        
        return metrics


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Run the scheduling simulation"""
    print("="*80)
    print("BATCH PLANT SCHEDULING SIMULATION")
    print("="*80)

    # Display plant configuration
    print("\n📦 EQUIPMENT:")
    for eq in PlantData.EQUIPMENT:
        print(f"  {eq}")

    print("\n🧪 PRODUCTS:")
    for prod in PlantData.PRODUCTS:
        print(f"  {prod}")
        for step in prod.recipe:
            print(f"    → {step}")

    print("\n📋 ORDERS:")
    total_demand = 0
    for order in PlantData.ORDERS:
        print(f"  {order}")
        total_demand += order.quantity
    print(f"  TOTAL DEMAND: {total_demand} kg")

    print("\n⏱️  CHANGEOVER TIMES (hours):")
    print("     ", "  ".join(f"{p.id:>4}" for p in PlantData.PRODUCTS))
    for p1 in PlantData.PRODUCTS:
        row = f"  {p1.id}"
        for p2 in PlantData.PRODUCTS:
            time = PlantData.CHANGEOVERS.get_time(p1.id, p2.id)
            row += f"  {time:4.1f}"
        print(row)

    # Create scheduler and simulate
    print("\n" + "="*80)
    print("COMPARING SCHEDULING HEURISTICS")
    print("="*80)

    scheduler = ProductionScheduler(PlantData)

    # Test different scheduling algorithms
    algorithms = [
        ("FIFO", scheduler.create_schedule_simple_fifo),
        ("EDD", scheduler.create_schedule_edd),
        ("Critical Ratio", scheduler.create_schedule_cr),
    ]

    results = []
    algorithm_results = []

    for algo_name, algo_func in algorithms:
        print(f"\n{'='*80}")
        print(f"ALGORITHM: {algo_name}")
        print(f"{'='*80}")

        schedule = algo_func()
        print(f"📅 Generated schedule with {len(schedule)} batches")

        metrics = scheduler.simulate_schedule(schedule)
        results.append((algo_name, metrics))

        # Prepare algorithm results for JSON
        order_details = []
        for order_id, details in sorted(metrics['order_completion'].items()):
            order_details.append({
                "order_id": order_id,
                "completion_day": round(details['completion_day'], 2),
                "due_day": details['due_day'],
                "tardiness_days": round(details['tardiness_days'], 2),
                "num_batches": details['num_batches']
            })

        algorithm_result = {
            "algorithm": algo_name,
            "makespan": round(metrics['makespan'], 2),
            "total_tardiness": round(metrics['total_tardiness'], 2),
            "late_orders": metrics['num_late_orders'],
            "order_details": order_details,
            "utilization": metrics['utilization']
        }
        algorithm_results.append(algorithm_result)

        print(f"\n⏰ Makespan: {metrics['makespan']:.2f} days")
        print(f"⚠️  Total Tardiness: {metrics['total_tardiness']:.2f} days")
        print(f"📉 Late Orders: {metrics['num_late_orders']} / {len(PlantData.ORDERS)}")

        print("\n📊 Order Completion Status:")
        for order_id, details in sorted(metrics['order_completion'].items()):
            status = "✅ ON TIME" if details['tardiness_days'] == 0 else f"❌ LATE by {details['tardiness_days']:.1f}d"
            print(f"  Order {order_id}: Completed day {details['completion_day']:.1f} "
                  f"(due: {details['due_day']:.1f}) {status}")

    # Analyze bottlenecks
    bottlenecks = analyze_bottlenecks(results, PlantData.ORDERS)

    # Prepare plant configuration for JSON
    plant_config = {
        "equipment": [
            {
                "id": eq.id,
                "type": eq.type,
                "capacity": eq.capacity
            } for eq in PlantData.EQUIPMENT
        ],
        "products": [
            {
                "id": prod.id,
                "name": prod.name,
                "batch_size": prod.batch_size,
                "total_processing_time": prod.total_processing_time(),
                "recipe": [
                    {
                        "step_name": step.step_name,
                        "equipment_type": step.equipment_type,
                        "duration": step.duration
                    } for step in prod.recipe
                ]
            } for prod in PlantData.PRODUCTS
        ],
        "orders": [
            {
                "id": order.id,
                "product_id": order.product_id,
                "quantity": order.quantity,
                "due_date": order.due_date,
                "priority": order.priority
            } for order in PlantData.ORDERS
        ]
    }

    # Create complete results structure
    simulation_results = {
        "plant_config": plant_config,
        "algorithm_results": algorithm_results,
        "bottlenecks": bottlenecks
    }

    # Save to JSON file
    with open('simulation_results.json', 'w') as f:
        json.dump(simulation_results, f, indent=2)

    print("\n💾 Results saved to simulation_results.json")

    # Compare results
    print("\n" + "="*80)
    print("COMPARISON SUMMARY")
    print("="*80)
    print(f"\n{'Algorithm':<30} {'Makespan':<12} {'Tardiness':<12} {'Late Orders'}")
    print("-" * 80)

    best_tardiness = min(r[1]['total_tardiness'] for r in results)

    for algo_name, metrics in results:
        is_best = " ⭐ BEST" if metrics['total_tardiness'] == best_tardiness else ""
        print(f"{algo_name:<30} {metrics['makespan']:>6.2f} days  "
              f"{metrics['total_tardiness']:>6.2f} days  "
              f"{metrics['num_late_orders']:>2} / {len(PlantData.ORDERS)}{is_best}")

    print("\n" + "="*80)
    # print("KEY INSIGHTS:")
    # print("="*80)
    # print("• Different schedules can significantly impact tardiness")
    # print("• EDD often performs well for minimizing late orders")
    # print("• Critical Ratio considers both urgency and processing time")
    # print("• Next step: Use OR-Tools CP-SAT for true optimization")
    # print("="*80)


def analyze_bottlenecks(results, orders):
    """Analyze bottlenecks across all algorithms"""
    # Find the algorithm with best performance (lowest tardiness)
    best_result = min(results, key=lambda x: x[1]['total_tardiness'])
    best_metrics = best_result[1]

    # Find most utilized equipment
    max_util = 0
    bottleneck_equip = None
    for equip_type, util_str in best_metrics['utilization'].items():
        util_pct = float(util_str.rstrip('%'))
        if util_pct > max_util:
            max_util = util_pct
            bottleneck_equip = equip_type

    # Find orders that are most constraining (highest tardiness)
    constraining_orders = []
    if best_metrics['order_completion']:
        # Sort orders by tardiness and take top 2
        sorted_orders = sorted(
            best_metrics['order_completion'].items(),
            key=lambda x: x[1]['tardiness_days'],
            reverse=True
        )
        constraining_orders = [int(order_id) for order_id, _ in sorted_orders[:2]]

    return {
        "equipment": bottleneck_equip,
        "utilization": round(max_util / 100, 2),  # Convert to decimal
        "constraining_orders": constraining_orders
    }
    

if __name__ == "__main__":
    main()
