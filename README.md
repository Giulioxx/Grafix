Grafix

Grafix is a small desktop application for geometry and function plotting, written in Python using Tkinter for the user interface and matplotlib for rendering. The idea is to create a minimal version of software like GeoGebra: users can draw points, line segments, lines, and circles on a Cartesian plane, plot functions and equations, and perform basic geometric constructions such as midpoints, intersections, and distance calculations.

This project was developed entirely on my own as an end-of-school-year project.

---

How to Run

You need Python 3.10+ and the following libraries:

pip install numpy matplotlib

("tkinter" is included in most Python installations on Windows. On Linux, you may need to install it using "sudo apt install python3-tk".)

To launch the application, run:

python main.py

---

Code Structure

The project is divided into five files, each with a specific purpose:

- "main.py" — Entry point: creates the Tkinter window and launches the application.
- "app.py" — The core of the application. It builds the interface, maintains the list of objects (points, lines, circles, functions, and implicit curves), interprets commands entered in the formula input box, and contains the main mathematical logic (intersections, distances, root finding, and calculator).
- "graph_canvas.py" — Manages the Cartesian plane, including object rendering, zooming, panning, and mouse interactions such as selecting and creating points, segments, lines, and circles. It also handles selection menus when multiple objects are close to each other.
- "models.py" — Defines the classes representing geometric objects: "Point", "Line", "Circle", "FunctionPlot", and "ImplicitPlot". It also contains the restricted environment for evaluating mathematical expressions, with supported functions such as "sin", "cos", "sqrt", and "log".
- "utils.py" — Contains "ExpressionHelper", the formula parser that converts user input (e.g. "2x^2", "√x", "log2(x)") into expressions that Python can evaluate.

---

How It Works

The Toolbar (Drawing Modes)

Each button activates a specific mode, changing what happens when the user clicks on the graph:

- Move — Pans the view by dragging and allows objects to be selected.
- New Point / Segment / Line / Circle — Creates the selected object by clicking on the plane.
- Midpoint — Calculates the midpoint of a segment.
- Intersection — Finds the intersection points between two objects.
- Distance — Measures the distance between two objects.

Additional buttons allow users to change the selected object's color, reset the view to its initial state, and delete the selected object.

The Formula Input Box

On the left side of the interface, users can enter commands and equations directly. The application automatically determines the type of object to create:

Input| Result
"A(1,2)" or "A=(1,2)"| A point named A
"line(A,B)" or "retta(A,B)"| A line passing through two existing points
"circle(cx,cy,r)"| A circle defined by its center and radius
"y = 2x+3", "y = sin(x)"| An explicit function
"x^2 + y^2 = 9"| A circle, recognized in canonical form
"x^2/4 + y^2/9 = 1"| An ellipse or implicit curve
General equations containing "="| An implicit curve of the form F(x,y) = 0

The formula parser ("ExpressionHelper") supports several convenient features, including "^" for exponentiation, implicit multiplication ("2x" → "2*x"), square roots without parentheses ("sqrt4"), the "√" symbol, and logarithms with arbitrary bases ("log2(x)", "log10(x)").

The Mathematical Engine

- Intersections: Line–line, line–circle, and circle–circle intersections are solved analytically. Intersections involving functions or implicit curves are calculated numerically by finding roots using a robust method (Brent bracketing, with damped Newton as a fallback). For implicit curves, the plane is sampled using the marching squares algorithm.
- Distance calculations: Supports distances between points, point–line pairs (with proper handling of line segments), point/line–circle pairs, circle–circle pairs, and parallel lines. First-degree functions ("y = mx + q") and linear implicit equations are also automatically recognized and treated as lines.
- Calculator: Located in the bottom-left corner, it evaluates numerical expressions using the same mathematical functions available throughout the application.

---

Known Limitations and Potential Bugs

The application was developed entirely on my own, so not every feature could be thoroughly tested or fully polished. Here are some known limitations to keep in mind:

- Distance calculations only support linear objects and circles. Distances between arbitrary curves (e.g. a parabola and a circle) are not supported. In these cases, the application reports that the selected pair is unsupported.
- Intersections involving functions and implicit curves are calculated numerically, so the results are approximate. In edge cases such as tangencies, asymptotes, densely packed curves, or very steep sections, some intersections may be missed or, more rarely, false intersections may be detected.
- The formula parser relies on heuristics, especially when handling implicit multiplication. Unusual expressions may be interpreted differently than expected. When in doubt, use parentheses to make the intended calculation clear.
- Performance: With many curves on screen or a wide zoom range, redrawing may become slower because some elements are recalculated or resampled during each update.
- Other undiscovered bugs may also exist.

If you encounter a problem, please report it. Every report helps improve the application.

---

Bug Reports and Contact

- Email: giuliooxx@gmail.com
- Telegram: "@itsmegiulioxx" (https://t.me/itsmegiulioxx)

When reporting a bug, please describe what you were doing, what you entered or clicked, and what happened. If possible, include any error message printed in the console, as it can be extremely helpful for troubleshooting.

---
