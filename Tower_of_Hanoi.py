import turtle
import time
import sys

# --- Configuration ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
PEG_X_COORDS = [-200, 0, 200]   # X-coordinates for the 3 pegs
BASE_Y = -200                   # Y-coordinate for the base of the pegs
PEG_HEIGHT = 300                # Height of the peg lines
DISK_HEIGHT = 25                # Height of each disk visually
# DISK_MAX_WIDTH_FACTOR = 18    # <<< We'll use this as an *upper limit*, but calculate dynamically
DISK_ABSOLUTE_MAX_FACTOR = 18   # Renamed: An absolute upper bound safety limit
DISK_MIN_WIDTH_FACTOR = 2       # Min width factor for the smallest disk (can adjust)
PEG_SPACING_SAFETY_FACTOR = 0.9 # Use 90% of space between peg centers for max disk width

ANIMATION_SPEED = 0             # Turtle animation speed (0 is fastest, 1-10 speeds up)
MOVE_DELAY = 0.6                # Seconds to pause between moves (reduced slightly)
LIFT_HEIGHT = 50                # How high to lift disk above peg before moving

# Color palette for disks (will cycle through if more disks than colors)
DISK_COLORS = ["#FF5733", "#33FF57", "#3357FF", "#FF33F6",
               "#F6FF33", "#33FFF6", "#8F33FF", "#FF8F33",
               "#FFBD33", "#33FFBD", "#BD33FF"] # Added more colors

# --- Global Variables ---
screen = None
pen = None
disks = {}
pegs_state = []
peg_y_tops = []
moves = []

def hanoi_solver (start, source, target):
    if start[source] == 1:
        start[source] -= 1
        start[target] += 1
        moves.append((source+1, target+1))
        return start
    else:
        start[source] -= 1
        target = 3 - (source+target)
        start = hanoi_solver(start, source, target)
        start[source] += 1 
        target = 3 - (source+target)
        start = hanoi_solver(start, source, target)
        start[target] -= 1
        source = 3 - (source+target)
        start = hanoi_solver(start, source, target)
        start[target] += 1
        return start
# --- Turtle Drawing Functions ---

def setup_screen():
    global screen
    screen = turtle.Screen()
    screen.setup(SCREEN_WIDTH, SCREEN_HEIGHT)
    screen.bgcolor("white")
    screen.title("Tower of Hanoi Visualizer")
    screen.tracer(0)

def draw_pegs():
    global pen, peg_y_tops
    pen = turtle.Turtle()
    pen.hideturtle()
    pen.penup()
    pen.speed(0)
    pen.pensize(5)
    pen.color("black")

    # Calculate dynamic base width based on peg spacing
    peg_spacing = abs(PEG_X_COORDS[1] - PEG_X_COORDS[0])
    base_width_extension = peg_spacing * 0.8 # Extend base beyond outer pegs

    pen.goto(PEG_X_COORDS[0] - base_width_extension, BASE_Y)
    pen.pendown()
    pen.goto(PEG_X_COORDS[2] + base_width_extension, BASE_Y)
    pen.penup()

    for x in PEG_X_COORDS:
        pen.goto(x, BASE_Y)
        pen.pendown()
        pen.goto(x, BASE_Y + PEG_HEIGHT)
        pen.penup()

    peg_y_tops = [BASE_Y + DISK_HEIGHT / 2] * 3
    screen.update()

# MODIFIED create_disks to accept calculated max_stretch_len
def create_disks(disk_count, max_stretch_len):
    """Creates turtle objects for each disk and positions them initially."""
    global disks, pegs_state, peg_y_tops
    disks = {}
    pegs_state = [[], [], []]
    peg_y_tops = [BASE_Y + DISK_HEIGHT / 2] * 3

    if disk_count == 0:
        return

    # Use a consistent minimum stretch length factor
    min_stretch_len = DISK_MIN_WIDTH_FACTOR

    # Ensure min_stretch_len is not greater than max_stretch_len
    min_stretch_len = min(min_stretch_len, max_stretch_len * 0.8) # Make min relative if max is very small
    min_stretch_len = max(0.5, min_stretch_len) # Ensure min width is not ridiculously tiny or zero


    for i in range(disk_count, 0, -1):
        disk_size = i
        disk_turtle = turtle.Turtle()
        disk_turtle.penup()
        disk_turtle.shape("square")
        disk_turtle.speed(ANIMATION_SPEED)

        # Calculate width factor using the DYNAMIC max_stretch_len passed in
        if disk_count > 1:
            # Linear interpolation between min_stretch_len and max_stretch_len
             width_factor = min_stretch_len + \
                           (max_stretch_len - min_stretch_len) * (disk_size - 1) / (disk_count - 1)
        else: # Handle single disk case
             width_factor = (min_stretch_len + max_stretch_len) / 2

        # Ensure width_factor is positive
        width_factor = max(0.1, width_factor) # Avoid zero or negative width

        # Apply stretch factors correctly (width = horizontal = stretch_len)
        disk_turtle.shapesize(stretch_wid=DISK_HEIGHT / 20.0, stretch_len=width_factor)

        disk_turtle.color(DISK_COLORS[(disk_size - 1) % len(DISK_COLORS)])
        disks[disk_size] = disk_turtle

        target_x = PEG_X_COORDS[0]
        target_y = peg_y_tops[0]
        disk_turtle.goto(target_x, target_y)

        pegs_state[0].append(disk_size)
        peg_y_tops[0] += DISK_HEIGHT

    screen.update()


def move_disk_visual(disk_size, start_peg_idx, end_peg_idx):
    """Animates the movement of a single disk turtle."""
    if disk_size not in disks:
        print(f"Error: Disk {disk_size} turtle not found!")
        return

    disk_turtle = disks[disk_size]
    start_x = PEG_X_COORDS[start_peg_idx]
    end_x = PEG_X_COORDS[end_peg_idx]

    # Use the current top of the stack for lift calculation
    # The disk being moved is AT peg_y_tops[start_peg_idx] - DISK_HEIGHT/2 effectively
    # So its top is peg_y_tops[start_peg_idx]
    current_disk_y = peg_y_tops[start_peg_idx] - DISK_HEIGHT / 2
    lift_y = max(peg_y_tops[start_peg_idx], peg_y_tops[end_peg_idx]) + LIFT_HEIGHT # Lift above highest point

    disk_turtle.goto(start_x, lift_y)
    screen.update()

    disk_turtle.goto(end_x, lift_y)
    screen.update()

    target_y = peg_y_tops[end_peg_idx]
    disk_turtle.goto(end_x, target_y)
    screen.update()

    # Update the logical top Y-coordinates
    peg_y_tops[start_peg_idx] -= DISK_HEIGHT
    peg_y_tops[end_peg_idx] += DISK_HEIGHT

# --- Main Simulation Logic ---
# --- Main Simulation Logic ---
def simulate_hanoi_gui(disk_count, moves):
    """Runs the Tower of Hanoi simulation with GUI."""
    if disk_count < 0:
        print("Error: Disk count must be non-negative.")
        if screen: turtle.bye()
        return

    try:
        setup_screen()
        draw_pegs() # Draws pegs using 'pen' - this is now permanent unless 'pen' is cleared

        # --- Calculate dynamic max width factor ---
        peg_spacing = abs(PEG_X_COORDS[1] - PEG_X_COORDS[0])
        max_allowed_visual_width = peg_spacing * PEG_SPACING_SAFETY_FACTOR
        calculated_max_stretch_len = max_allowed_visual_width / 20.0
        actual_max_stretch_len = min(calculated_max_stretch_len, DISK_ABSOLUTE_MAX_FACTOR)
        actual_max_stretch_len = max(actual_max_stretch_len, DISK_MIN_WIDTH_FACTOR + 0.5)
        print(f"Peg Spacing: {peg_spacing}, Max Visual Disk Width Allowed: {max_allowed_visual_width:.2f}, Effective Max Stretch Factor: {actual_max_stretch_len:.2f}")

        # Create disks using the calculated maximum stretch length
        create_disks(disk_count, actual_max_stretch_len)

        # --- Create a dedicated turtle for status text ---
        status_pen = turtle.Turtle()
        status_pen.hideturtle()
        status_pen.penup()
        status_pen.speed(0) # Make text appear instantly
        status_pen.color("black")
        status_text_y = SCREEN_HEIGHT * 0.4 # Position text higher up

        if disk_count == 0:
            print("No disks to move.")
            status_pen.goto(0, status_text_y) # Use status_pen
            status_pen.write("No disks to move. Finished!", align="center", font=("Arial", 16, "normal"))
            screen.update()
            time.sleep(3)
            turtle.bye()
            return

        # --- Display Initial State & Start Prompt ---
        status_pen.goto(0, status_text_y) # Use status_pen
        status_pen.write("Initial State. Press Enter to start...", align="center", font=("Arial", 16, "normal"))
        screen.update()
        input("Press Enter in the console to start the simulation...") # Wait for user
        status_pen.clear() # Clear only the text written by status_pen
        screen.update()
        time.sleep(0.5)


        # --- Process Moves ---
        move_counter = 0
        total_moves = len(moves)
        for start_peg, end_peg in moves:
            move_counter += 1
            status_pen.clear() # Use status_pen to clear previous text
            status_pen.goto(0, status_text_y) # Use status_pen to position text
            status_pen.write(f"Move {move_counter}/{total_moves}: {start_peg} -> {end_peg}", align="center", font=("Arial", 16, "normal"))
            screen.update() # Update screen to show new text

            # --- Validation (logical state check) ---
            # (Validation code remains the same)
            if not (1 <= start_peg <= 3 and 1 <= end_peg <= 3):
                print(f"Error: Invalid peg number in move {move_counter} ({start_peg} -> {end_peg}).")
                status_pen.write(f"Error: Invalid peg number {start_peg} -> {end_peg}", align="center", font=("Arial", 16, "normal")) # Optional error on screen
                screen.update()
                break
            start_idx = start_peg - 1
            end_idx = end_peg - 1
            if not pegs_state[start_idx]:
                print(f"Error in move {move_counter}: Logic error - trying to move from empty source peg {start_peg}.")
                print(f"Current Pegs State: {pegs_state}")
                status_pen.write(f"Error: Trying to move from empty peg {start_peg}", align="center", font=("Arial", 16, "normal")) # Optional error on screen
                screen.update()
                break
            disk_to_move_size = pegs_state[start_idx][-1]
            if pegs_state[end_idx] and disk_to_move_size > pegs_state[end_idx][-1]:
                 print(f"Error in move {move_counter}: Logic error - trying to place disk {disk_to_move_size} on smaller disk {pegs_state[end_idx][-1]} on peg {end_peg}.")
                 print(f"Current Pegs State: {pegs_state}")
                 status_pen.write(f"Error: Invalid move {disk_to_move_size} onto {pegs_state[end_idx][-1]}", align="center", font=("Arial", 16, "normal")) # Optional error on screen
                 screen.update()
                 break


            # --- Perform Visual Move ---
            move_disk_visual(disk_to_move_size, start_idx, end_idx)

            # --- Update Logical State ---
            disk = pegs_state[start_idx].pop()
            pegs_state[end_idx].append(disk)

            time.sleep(MOVE_DELAY)

        # --- Simulation End ---
        # Only clear and write the final message if no error broke the loop early
        if move_counter == total_moves:
            status_pen.clear() # Use status_pen
            status_pen.goto(0, status_text_y) # Use status_pen
            status_pen.write("Simulation Finished!", align="center", font=("Arial", 16, "bold"))
            screen.update()
            print("Simulation Finished!")
        else:
            print("Simulation Stopped Due to Error.")


        screen.mainloop() # Keep window open

    except turtle.Terminator:
        print("Turtle window closed by user.")
    except Exception as e:
        print(f"An error occurred during simulation: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # ... (finally block remains the same)
        try:
            if screen and screen._RUNNING and not screen.cv.winfo_exists():
                 turtle.bye()
        except:
            pass


if __name__ == "__main__":
    while True:
        try:
            num_disks_input = input("Enter the number of disks (e.g., 3): ")
            if not num_disks_input:
                 print("No input provided. Exiting.")
                 sys.exit()
            num_disks = int(num_disks_input)
            if num_disks < 0:
                 print("Please enter a non-negative number.")
                 continue
            if num_disks > 10: # Add a warning for large numbers
                print("Warning: More than 10 disks can be very slow!")
                cont = input("Continue anyway? (y/n): ").lower()
                if cont != 'y':
                    continue
            break
        except ValueError:
            print("Invalid input. Please enter an integer.")

    # --- Generate moves using the solver ---
    print(f"Generating moves for {num_disks} disks...")
    source = 0  # Peg 1
    target = 2  # Peg 3
    start = [0, 0, 0]
    start[source] = num_disks
    start[target] = 0
    hanoi_solver(start, source, target) # Standard: 1 -> 3 using 2
    solution_moves = moves.copy() # Copy the generated moves
    print(f"Total moves required: {2**num_disks - 1}")
    print(f"Moves: {solution_moves}")

    # --- Run the GUI Simulation ---
    simulate_hanoi_gui(num_disks, solution_moves)