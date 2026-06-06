# Makefile for WEEKS Microstrip Calculator with YAML Input
# Requires libyaml library
# Linux/Unix compatible

# Directories
SRC_DIR = src
INC_DIR = include
EXAMPLE_DIR = examples
BUILD_DIR = build
DOC_DIR = docs

# Compiler
CC = gcc

# Compiler flags
CFLAGS = -Wall -O2 -g -I$(INC_DIR)
INCLUDES = -I$(INC_DIR) -I/usr/local/include -I/usr/include -I/usr/include/meschach
LDFLAGS = -L/usr/local/lib -L/usr/lib
LIBS = -lmeschach -lyaml -lm

# Source files
SOURCES = $(SRC_DIR)/weeks.c \
          $(SRC_DIR)/build.c \
          $(SRC_DIR)/calcl.c \
          $(SRC_DIR)/input.c \
          $(SRC_DIR)/lpp.c

# Object files
OBJECTS = $(SOURCES:$(SRC_DIR)/%.c=$(BUILD_DIR)/%.o)

# Executable
TARGET = weeks

# Default target
all: $(BUILD_DIR) $(TARGET)

# Create build directory
$(BUILD_DIR):
	mkdir -p $(BUILD_DIR)

# Link executable
$(TARGET): $(OBJECTS)
	$(CC) $(LDFLAGS) -o $@ $^ $(LIBS)
	@echo ""
	@echo "========================================"
	@echo "Build complete: $(TARGET)"
	@echo "========================================"
	@echo "Run with: ./$(TARGET)"
	@echo ""
	@echo "Input file: test.yaml (YAML format)"
	@echo "Example files in $(EXAMPLE_DIR)/"
	@echo ""
	@echo "To run examples:"
	@echo "  make test-fr4     - FR4 substrate"
	@echo "  make test-air     - Air baseline"
	@echo "  make test-rogers  - Rogers RO4003C"
	@echo ""

# Compile source files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.c
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# Clean build artifacts
clean:
	rm -rf $(BUILD_DIR) $(TARGET)
	@echo "Cleaned build artifacts"

# Deep clean
distclean: clean
	rm -f *.exe *.out *.log *~
	@echo "Deep clean complete"

# Install
install: $(TARGET)
	install -m 755 $(TARGET) /usr/local/bin/
	@echo "Installed to /usr/local/bin/weeks"

# Uninstall
uninstall:
	rm -f /usr/local/bin/$(TARGET)
	@echo "Uninstalled from /usr/local/bin"

# Run with FR4
test-fr4: $(TARGET)
	@echo "Running with FR4 substrate..."
	@cp $(EXAMPLE_DIR)/test_fr4.yaml test.yaml
	./$(TARGET)

# Run with air
test-air: $(TARGET)
	@echo "Running with air (baseline)..."
	@cp $(EXAMPLE_DIR)/test_air.yaml test.yaml
	./$(TARGET)

# Run with Rogers
test-rogers: $(TARGET)
	@echo "Running with Rogers RO4003C substrate..."
	@cp $(EXAMPLE_DIR)/test_rogers4003.yaml test.yaml
	./$(TARGET)

# Cross-check weeks R/L against FastHenry
check-fasthenry: $(TARGET)
	@command -v fasthenry >/dev/null || { echo "FastHenry not found — see docs/fasthenry-crosscheck.md"; exit 1; }
	python3 -m tools.fh_crosscheck examples/test_single.yaml
	python3 -m tools.fh_crosscheck examples/test_fr4.yaml

# Check dependencies
check-deps:
	@echo "Checking required libraries..."
	@echo -n "Meschach: "
	@ldconfig -p | grep -q libmeschach && echo "Found" || echo "NOT FOUND - install libmeschach-dev"
	@echo -n "libyaml: "
	@pkg-config --exists yaml-0.1 && echo "Found" || echo "NOT FOUND - install libyaml-dev"

# Help
help:
	@echo "WEEKS Microstrip Calculator with YAML Input"
	@echo ""
	@echo "REQUIREMENTS:"
	@echo "  - Meschach library (libmeschach-dev)"
	@echo "  - libyaml library (libyaml-dev)"
	@echo ""
	@echo "Install dependencies:"
	@echo "  Ubuntu/Debian: sudo apt-get install libmeschach-dev libyaml-dev"
	@echo "  Fedora/RHEL:   sudo dnf install meschach-devel libyaml-devel"
	@echo ""
	@echo "Targets:"
	@echo "  make              - Build executable"
	@echo "  make check-deps   - Check if libraries are installed"
	@echo "  make clean        - Remove build artifacts"
	@echo "  make distclean    - Remove all generated files"
	@echo "  make test-fr4     - Run with FR4 substrate"
	@echo "  make test-air     - Run with air baseline"
	@echo "  make test-rogers  - Run with Rogers material"
	@echo "  make install      - Install to /usr/local/bin"
	@echo "  make tree         - Show project structure"
	@echo "  make help         - Show this help"
	@echo ""
	@echo "Input Format:"
	@echo "  YAML files with frequency and conductor definitions"
	@echo "  See examples/ directory for samples"

# Show structure
tree:
	@echo "Project Structure:"
	@echo "."
	@echo "├── README.md"
	@echo "├── Makefile"
	@echo "├── $(SRC_DIR)/               (Source files - YAML input support)"
	@echo "│   ├── weeks.c"
	@echo "│   ├── input.c        (YAML parser using libyaml)"
	@echo "│   └── ..."
	@echo "├── $(INC_DIR)/           (Headers)"
	@echo "├── $(EXAMPLE_DIR)/       (YAML examples)"
	@echo "│   ├── test.yaml      (default - FR4)"
	@echo "│   ├── test_air.yaml"
	@echo "│   ├── test_fr4.yaml"
	@echo "│   └── test_rogers4003.yaml"
	@echo "└── $(BUILD_DIR)/            (Build artifacts)"

.PHONY: all clean distclean install uninstall test-fr4 test-air test-rogers check-fasthenry check-deps help tree
