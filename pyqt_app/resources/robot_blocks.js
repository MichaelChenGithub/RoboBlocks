(function(global) {
    function init() {
        const Blockly = global.Blockly;
        if (!Blockly) {
            console.error('Blockly is not loaded. Ensure blockly.min.js is reachable.');
            return;
        }

    const CATEGORY_LOGIC = {
        kind: 'category',
        name: 'Logic',
        colour: '#5C81A6',
        contents: [
            { kind: 'block', type: 'controls_if' },
            { kind: 'block', type: 'logic_compare' },
            { kind: 'block', type: 'logic_operation' },
            { kind: 'block', type: 'logic_negate' },
            { kind: 'block', type: 'logic_boolean' },
            { kind: 'block', type: 'logic_null' },
            { kind: 'block', type: 'logic_ternary' }
        ]
    };

    const CATEGORY_LOOPS = {
        kind: 'category',
        name: 'Loops',
        colour: '#5CA65C',
        contents: [
            { kind: 'block', type: 'controls_repeat_ext' },
            { kind: 'block', type: 'controls_whileUntil' },
            { kind: 'block', type: 'controls_for' },
            { kind: 'block', type: 'controls_flow_statements' }
        ]
    };

    const CATEGORY_MATH = {
        kind: 'category',
        name: 'Math',
        colour: '#5C68A6',
        contents: [
            { kind: 'block', type: 'math_number' },
            { kind: 'block', type: 'math_arithmetic' },
            { kind: 'block', type: 'math_single' },
            { kind: 'block', type: 'math_trig' },
            { kind: 'block', type: 'math_constant' },
            { kind: 'block', type: 'math_round' },
            { kind: 'block', type: 'math_modulo' },
            { kind: 'block', type: 'math_constrain' },
            { kind: 'block', type: 'math_random_int' },
            { kind: 'block', type: 'math_random_float' }
        ]
    };

    const CATEGORY_TEXT = {
        kind: 'category',
        name: 'Text',
        colour: '#A6745C',
        contents: [
            { kind: 'block', type: 'text' },
            { kind: 'block', type: 'text_join' },
            { kind: 'block', type: 'text_length' },
            { kind: 'block', type: 'text_isEmpty' },
            { kind: 'block', type: 'text_indexOf' },
            { kind: 'block', type: 'text_charAt' },
            { kind: 'block', type: 'text_getSubstring' },
            { kind: 'block', type: 'text_changeCase' },
            { kind: 'block', type: 'text_trim' },
            { kind: 'block', type: 'text_print' }
        ]
    };

    const CATEGORY_VARIABLES = {
        kind: 'category',
        name: 'Variables',
        custom: 'VARIABLE',
        colour: '#A65C81'
    };

    const CATEGORY_FUNCTIONS = {
        kind: 'category',
        name: 'Functions',
        custom: 'PROCEDURE',
        colour: '#5CA699'
    };

    const CATEGORY_ACTIONS = {
        kind: 'category',
        name: 'Robot Actions',
        colour: '#5C81A6',
        contents: [
            { kind: 'block', type: 'connect_robot' },
            { kind: 'block', type: 'disconnect_robot' },
            { kind: 'block', type: 'power_on_servo' },
            { kind: 'block', type: 'power_off_servo' },
            { kind: 'block', type: 'set_speed' },
            { kind: 'block', type: 'set_acceleration' },
            { kind: 'block', type: 'move_to' },
            { kind: 'block', type: 'move_joint' },
            { kind: 'block', type: 'move_linear' },
            { kind: 'block', type: 'move_circular' },
            { kind: 'block', type: 'stop_motion' },
            { kind: 'block', type: 'wait_for_move_finish' },
            { kind: 'block', type: 'set_tool_coordinate' },
            { kind: 'block', type: 'set_user_coordinate' },
            { kind: 'block', type: 'grab' },
            { kind: 'block', type: 'release' },
            { kind: 'block', type: 'print_numbers' }
        ]
    };

    const CATEGORY_QUERIES = {
        kind: 'category',
        name: 'Robot Queries',
        colour: '#a65c81',
        contents: [
            { kind: 'block', type: 'get_current_joint_position' },
            { kind: 'block', type: 'get_current_cartesian_position' },
            { kind: 'block', type: 'get_robot_status' },
            { kind: 'block', type: 'get_digital_input' }
        ]
    };

    const CATEGORY_IO = {
        kind: 'category',
        name: 'Digital IO',
        colour: '#5ca65c',
        contents: [
            { kind: 'block', type: 'set_digital_output' }
        ]
    };

    const CATEGORY_METADATA = {
        kind: 'category',
        name: 'Metadata',
        colour: '#aa8f39',
        contents: [
            { kind: 'block', type: 'set_metadata' }
        ]
    };

        Blockly.RobotToolbox = JSON.stringify({
        kind: 'categoryToolbox',
            contents: [
                CATEGORY_METADATA,
                CATEGORY_ACTIONS,
                CATEGORY_IO,
                CATEGORY_QUERIES,
                CATEGORY_LOGIC,
                CATEGORY_LOOPS,
                CATEGORY_MATH
            ]
    });

        function createBlock(type, color, initFn) {
        Blockly.Blocks[type] = {
            init: function() {
                this.setColour(color);
                initFn.call(this);
                this.setPreviousStatement(true, null);
                this.setNextStatement(true, null);
                this.setTooltip(type.replace(/_/g, ' '));
            }
        };
    }

        function addNumberField(block, name, label, defaultValue) {
        block.appendDummyInput()
            .appendField(label)
            .appendField(new Blockly.FieldNumber(defaultValue || 0), name);
    }

        function addTextField(block, name, label, defaultValue) {
        block.appendDummyInput()
            .appendField(label)
            .appendField(new Blockly.FieldTextInput(defaultValue || ''), name);
    }

        function addCheckboxField(block, name, label) {
        block.appendDummyInput()
            .appendField(label)
            .appendField(new Blockly.FieldCheckbox('FALSE'), name);
    }

        // Metadata block
        Blockly.Blocks['set_metadata'] = {
        init: function() {
            this.setColour('#aa8f39');
            this.appendDummyInput().appendField('Workflow metadata');
            this.appendDummyInput()
                .appendField('Robot brand')
                .appendField(new Blockly.FieldDropdown([
                    ['Default', 'default'],
                    ['Fanuc', 'fanuc'],
                    ['Kuka', 'kuka']
                ]), 'ROBOT_BRAND');
            addTextField(this, 'NAMESPACE', 'Namespace', 'GeneratedWorkflows');
            addTextField(this, 'CLASS_NAME', 'Class name', 'RobotProgram');
            addTextField(this, 'METHOD_NAME', 'Method', 'Run');
            addCheckboxField(this, 'ATTACH_LOGGER', 'Attach console logger');
            this.setPreviousStatement(false, null);
        }
        };

        // Basic connection and power blocks
        createBlock('connect_robot', '#5C81A6', function() {
        addTextField(this, 'IP', 'IP address', '192.168.0.10');
        addNumberField(this, 'PORT', 'Port', 60008);
        addNumberField(this, 'TIMEOUT', 'Timeout (ms)', 5000);
    });

    createBlock('disconnect_robot', '#5C81A6', function() {
        this.appendDummyInput().appendField('Disconnect robot');
    });

    createBlock('power_on_servo', '#5C81A6', function() {
        this.appendDummyInput().appendField('Power on servo');
    });

    createBlock('power_off_servo', '#5C81A6', function() {
        this.appendDummyInput().appendField('Power off servo');
    });

    createBlock('set_speed', '#5C81A6', function() {
        addNumberField(this, 'PERCENTAGE', 'Speed %', 50);
    });

    createBlock('set_acceleration', '#5C81A6', function() {
        addNumberField(this, 'PERCENTAGE', 'Acceleration %', 50);
    });

    createBlock('move_to', '#5C81A6', function() {
        this.appendDummyInput().appendField('Move to XYZ');
        addNumberField(this, 'X', 'X', 0);
        addNumberField(this, 'Y', 'Y', 0);
        addNumberField(this, 'Z', 'Z', 0);
        addNumberField(this, 'SPEED', 'Speed %', 50);
    });

    createBlock('move_joint', '#5C81A6', function() {
        this.appendDummyInput().appendField('Move joint');
        ['J1','J2','J3','J4','J5','J6'].forEach((axis, idx) => {
            addNumberField(this, axis, axis, 0);
        });
        addNumberField(this, 'SPEED', 'Speed %', 50);
    });

    createBlock('move_linear', '#5C81A6', function() {
        this.appendDummyInput().appendField('Move linear');
        ['X','Y','Z','RX','RY','RZ'].forEach(axis => {
            addNumberField(this, axis, axis, 0);
        });
        addNumberField(this, 'SPEED', 'Speed %', 50);
    });

    createBlock('move_circular', '#5C81A6', function() {
        this.appendDummyInput().appendField('Move circular');
        this.appendDummyInput().appendField('Via point');
        ['VX','VY','VZ','VRX','VRY','VRZ'].forEach(axis => {
            addNumberField(this, axis, axis, 0);
        });
        this.appendDummyInput().appendField('End point');
        ['EX','EY','EZ','ERX','ERY','ERZ'].forEach(axis => {
            addNumberField(this, axis, axis, 0);
        });
    });

    createBlock('stop_motion', '#5C81A6', function() {
        this.appendDummyInput().appendField('Stop motion');
        addTextField(this, 'STOP_TYPE', 'Stop type', '');
    });

    createBlock('wait_for_move_finish', '#5C81A6', function() {
        this.appendDummyInput().appendField('Wait for move finish');
        addNumberField(this, 'TIMEOUT', 'Timeout (ms)', 0);
    });

    createBlock('set_tool_coordinate', '#5C81A6', function() {
        this.appendDummyInput().appendField('Set tool coordinate');
        ['TX','TY','TZ','TRX','TRY','TRZ'].forEach(axis => {
            addNumberField(this, axis, axis, 0);
        });
    });

    createBlock('set_user_coordinate', '#5C81A6', function() {
        this.appendDummyInput().appendField('Set user coordinate');
        ['UX','UY','UZ','URX','URY','URZ'].forEach(axis => {
            addNumberField(this, axis, axis, 0);
        });
    });

    createBlock('grab', '#5C81A6', function() {
        this.appendDummyInput().appendField('Grab');
    });

    createBlock('release', '#5C81A6', function() {
        this.appendDummyInput().appendField('Release');
    });

    createBlock('print_numbers', '#5C81A6', function() {
        this.appendDummyInput().appendField('Print numbers');
    });

    // Query blocks
    createBlock('get_current_joint_position', '#a65c81', function() {
        this.appendDummyInput().appendField('Get current joint position');
        addTextField(this, 'STORE', 'Store as', 'jointPos');
    });

    createBlock('get_current_cartesian_position', '#a65c81', function() {
        this.appendDummyInput().appendField('Get current cartesian position');
        addTextField(this, 'STORE', 'Store as', 'cartPos');
    });

    createBlock('get_robot_status', '#a65c81', function() {
        this.appendDummyInput().appendField('Get robot status');
        addTextField(this, 'STORE', 'Store as', 'status');
    });

        createBlock('set_digital_output', '#5ca65c', function() {
        this.appendDummyInput().appendField('Set digital output');
        addNumberField(this, 'PORT', 'Port', 0);
        this.appendDummyInput()
            .appendField('Value')
            .appendField(new Blockly.FieldDropdown([
                ['False', 'FALSE'],
                ['True', 'TRUE']
            ]), 'VALUE');
    });

        createBlock('get_digital_input', '#a65c81', function() {
        this.appendDummyInput().appendField('Get digital input');
        addNumberField(this, 'PORT', 'Port', 0);
        addTextField(this, 'STORE', 'Store as', 'inputValue');
    });
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(init, 0);
    } else {
        document.addEventListener('DOMContentLoaded', init);
    }
})(window);
