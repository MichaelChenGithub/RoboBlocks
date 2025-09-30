(function(global) {
    function init() {
        const Blockly = global.Blockly;
        if (!Blockly) {
            console.error('Blockly is not loaded. Robot generator unavailable.');
            return;
        }

        const Generator = new Blockly.Generator('robot_ir');
        Generator.scrub_ = function() { return ''; };

        const commandsWithoutParameters = new Set([
            'disconnect_robot',
            'power_on_servo',
            'power_off_servo',
            'grab',
            'release',
            'print_numbers'
        ]);

        const parameterReaders = {
            connect_robot: block => ({
                ip_address: block.getFieldValue('IP') || '192.168.0.10',
                port: Number(block.getFieldValue('PORT') || 60008),
                timeout_ms: Number(block.getFieldValue('TIMEOUT') || 0),
            }),
            set_speed: block => ({ percentage: Number(block.getFieldValue('PERCENTAGE') || 0) }),
            set_acceleration: block => ({ percentage: Number(block.getFieldValue('PERCENTAGE') || 0) }),
            move_to: block => ({
                x: Number(block.getFieldValue('X') || 0),
                y: Number(block.getFieldValue('Y') || 0),
                z: Number(block.getFieldValue('Z') || 0),
                speed_percentage: Number(block.getFieldValue('SPEED') || 0),
            }),
            move_joint: block => ({
                j1: Number(block.getFieldValue('J1') || 0),
                j2: Number(block.getFieldValue('J2') || 0),
                j3: Number(block.getFieldValue('J3') || 0),
                j4: Number(block.getFieldValue('J4') || 0),
                j5: Number(block.getFieldValue('J5') || 0),
                j6: Number(block.getFieldValue('J6') || 0),
                speed_percentage: Number(block.getFieldValue('SPEED') || 0),
            }),
            move_linear: block => ({
                x: Number(block.getFieldValue('X') || 0),
                y: Number(block.getFieldValue('Y') || 0),
                z: Number(block.getFieldValue('Z') || 0),
                rx: Number(block.getFieldValue('RX') || 0),
                ry: Number(block.getFieldValue('RY') || 0),
                rz: Number(block.getFieldValue('RZ') || 0),
                speed_percentage: Number(block.getFieldValue('SPEED') || 0),
            }),
            move_circular: block => ({
                via_point: {
                    x: Number(block.getFieldValue('VX') || 0),
                    y: Number(block.getFieldValue('VY') || 0),
                    z: Number(block.getFieldValue('VZ') || 0),
                    rx: Number(block.getFieldValue('VRX') || 0),
                    ry: Number(block.getFieldValue('VRY') || 0),
                    rz: Number(block.getFieldValue('VRZ') || 0),
                },
                end_point: {
                    x: Number(block.getFieldValue('EX') || 0),
                    y: Number(block.getFieldValue('EY') || 0),
                    z: Number(block.getFieldValue('EZ') || 0),
                    rx: Number(block.getFieldValue('ERX') || 0),
                    ry: Number(block.getFieldValue('ERY') || 0),
                    rz: Number(block.getFieldValue('ERZ') || 0),
                },
            }),
            stop_motion: block => {
                const stop = block.getFieldValue('STOP_TYPE') || '';
                return stop ? { stop_type: stop } : {};
            },
            wait_for_move_finish: block => {
                const timeout = Number(block.getFieldValue('TIMEOUT') || 0);
                return timeout ? { timeout_ms: timeout } : {};
            },
            set_tool_coordinate: block => ({
                tool_data: ['TX','TY','TZ','TRX','TRY','TRZ'].map(k => Number(block.getFieldValue(k) || 0)),
            }),
            set_user_coordinate: block => ({
                user_data: ['UX','UY','UZ','URX','URY','URZ'].map(k => Number(block.getFieldValue(k) || 0)),
            }),
            get_current_joint_position: block => {
                const store = block.getFieldValue('STORE') || '';
                return store ? { store_as: store } : {};
            },
            get_current_cartesian_position: block => {
                const store = block.getFieldValue('STORE') || '';
                return store ? { store_as: store } : {};
            },
            get_robot_status: block => {
                const store = block.getFieldValue('STORE') || '';
                return store ? { store_as: store } : {};
            },
            set_digital_output: block => ({
                port: Number(block.getFieldValue('PORT') || 0),
                value: (block.getFieldValue('VALUE') || 'FALSE') === 'TRUE',
            }),
            get_digital_input: block => {
                const store = block.getFieldValue('STORE') || '';
                const params = { port: Number(block.getFieldValue('PORT') || 0) };
                if (store) { params.store_as = store; }
                return params;
            },
        };

        function blockId(block) {
            return block.data || block.id || Blockly.utils.idGenerator.genUid();
        }

        function expressionFrom(block) {
            if (!block) {
                return { expr_type: 'literal_number', value: 0 };
            }
            switch (block.type) {
                case 'math_number':
                    return { expr_type: 'literal_number', value: Number(block.getFieldValue('NUM') || 0) };
                case 'logic_boolean':
                    return { expr_type: 'literal_boolean', value: block.getFieldValue('BOOL') === 'TRUE' };
                case 'logic_compare':
                    return {
                        expr_type: 'comparison',
                        op: (block.getFieldValue('OP') || 'EQ').toLowerCase(),
                        left: expressionFrom(block.getInputTargetBlock('A')),
                        right: expressionFrom(block.getInputTargetBlock('B')),
                    };
                case 'logic_operation':
                    return {
                        expr_type: 'logic_binary',
                        op: (block.getFieldValue('OP') || 'AND').toLowerCase(),
                        left: expressionFrom(block.getInputTargetBlock('A')),
                        right: expressionFrom(block.getInputTargetBlock('B')),
                    };
                case 'logic_negate':
                    return {
                        expr_type: 'logic_not',
                        argument: expressionFrom(block.getInputTargetBlock('BOOL')),
                    };
                case 'logic_null':
                    return { expr_type: 'literal_null' };
                case 'logic_ternary':
                    return {
                        expr_type: 'ternary',
                        condition: expressionFrom(block.getInputTargetBlock('IF')),
                        when_true: expressionFrom(block.getInputTargetBlock('THEN')),
                        when_false: expressionFrom(block.getInputTargetBlock('ELSE')),
                    };
                case 'math_arithmetic':
                    return {
                        expr_type: 'arithmetic',
                        op: (block.getFieldValue('OP') || 'ADD').toLowerCase(),
                        left: expressionFrom(block.getInputTargetBlock('A')),
                        right: expressionFrom(block.getInputTargetBlock('B')),
                    };
                case 'math_single':
                    return {
                        expr_type: 'math_single',
                        op: (block.getFieldValue('OP') || 'ROOT').toLowerCase(),
                        argument: expressionFrom(block.getInputTargetBlock('NUM')),
                    };
                case 'math_trig':
                    return {
                        expr_type: 'math_trig',
                        op: (block.getFieldValue('OP') || 'SIN').toLowerCase(),
                        argument: expressionFrom(block.getInputTargetBlock('NUM')),
                    };
                case 'math_constant':
                    return {
                        expr_type: 'math_constant',
                        constant: (block.getFieldValue('CONSTANT') || 'PI').toLowerCase(),
                    };
                case 'math_round':
                    return {
                        expr_type: 'math_round',
                        op: (block.getFieldValue('OP') || 'ROUND').toLowerCase(),
                        argument: expressionFrom(block.getInputTargetBlock('NUM')),
                    };
                case 'math_modulo':
                    return {
                        expr_type: 'math_modulo',
                        left: expressionFrom(block.getInputTargetBlock('DIVIDEND')),
                        right: expressionFrom(block.getInputTargetBlock('DIVISOR')),
                    };
                case 'math_constrain':
                    return {
                        expr_type: 'math_constrain',
                        value: expressionFrom(block.getInputTargetBlock('VALUE')),
                        low: expressionFrom(block.getInputTargetBlock('LOW')),
                        high: expressionFrom(block.getInputTargetBlock('HIGH')),
                    };
                case 'math_random_int':
                    return {
                        expr_type: 'math_random_int',
                        low: expressionFrom(block.getInputTargetBlock('FROM')),
                        high: expressionFrom(block.getInputTargetBlock('TO')),
                    };
                case 'math_random_float':
                    return { expr_type: 'math_random_float' };
                default:
                    throw new Error('Unsupported expression block: ' + block.type);
            }
        }

        function sequenceFrom(block, metadata) {
            const nodes = [];
            let current = block;
            while (current) {
                if (current.type === 'set_metadata') {
                    applyMetadata(current, metadata);
                } else {
                    nodes.push(...convertStatementBlock(current, metadata));
                }
                current = current.getNextBlock();
            }
            return nodes;
        }

        function convertStatementBlock(block, metadata) {
            const type = block.type;
            if (type === 'controls_if') {
                return [convertIfBlock(block, metadata)];
            }
            if (type === 'controls_repeat_ext') {
                return [convertRepeatBlock(block, metadata)];
            }
            if (type === 'controls_whileUntil') {
                return [convertWhileBlock(block, metadata)];
            }
            if (type === 'controls_for' || type === 'controls_forEach') {
                return [convertForBlock(block, metadata)];
            }
            if (type === 'controls_flow_statements') {
                return [convertFlowStatement(block)];
            }

            if (parameterReaders[type] || commandsWithoutParameters.has(type)) {
                return [convertCommandBlock(block)];
            }

            console.warn('Ignoring unsupported statement block:', type);
            return [];
        }

        function applyMetadata(block, metadata) {
            metadata.robot_brand = block.getFieldValue('ROBOT_BRAND') || 'default';
            metadata.namespace = block.getFieldValue('NAMESPACE') || 'GeneratedWorkflows';
            metadata.class_name = block.getFieldValue('CLASS_NAME') || 'RobotProgram';
            metadata.method_name = block.getFieldValue('METHOD_NAME') || 'Run';
            metadata.attach_console_logger = block.getFieldValue('ATTACH_LOGGER') === 'TRUE';
        }

        function convertCommandBlock(block) {
            const commandName = block.type;
            const paramsReader = parameterReaders[commandName];
            const params = paramsReader ? paramsReader(block) : {};
            if (commandsWithoutParameters.has(commandName)) {
                return {
                    id: blockId(block),
                    node_type: 'command',
                    command: commandName,
                };
            }
            return {
                id: blockId(block),
                node_type: 'command',
                command: commandName,
                parameters: params,
            };
        }

        function convertIfBlock(block, metadata) {
            const branches = [];
            let index = 0;
            while (block.getInput('IF' + index)) {
                const conditionBlock = block.getInputTargetBlock('IF' + index);
                const doBlock = block.getInputTargetBlock('DO' + index);
                branches.push({
                    condition: expressionFrom(conditionBlock),
                    body: sequenceFrom(doBlock, metadata),
                });
                index += 1;
            }
            const elseBlock = block.getInputTargetBlock('ELSE');
            const elseBody = sequenceFrom(elseBlock, metadata);
            return {
                id: blockId(block),
                node_type: 'if',
                branches,
                else_branch: elseBody.length ? elseBody : undefined,
            };
        }

        function convertRepeatBlock(block, metadata) {
            const timesBlock = block.getInputTargetBlock('TIMES');
            const bodyBlock = block.getInputTargetBlock('DO');
            return {
                id: blockId(block),
                node_type: 'repeat',
                count: expressionFrom(timesBlock),
                body: sequenceFrom(bodyBlock, metadata),
            };
        }

        function convertWhileBlock(block, metadata) {
            const boolBlock = block.getInputTargetBlock('BOOL');
            const bodyBlock = block.getInputTargetBlock('DO');
            const mode = block.getFieldValue('MODE') === 'UNTIL' ? 'until' : 'while';
            return {
                id: blockId(block),
                node_type: 'while',
                mode,
                condition: expressionFrom(boolBlock),
                body: sequenceFrom(bodyBlock, metadata),
            };
        }

        function convertForBlock(block, metadata) {
            if (block.type === 'controls_for') {
                return {
                    id: blockId(block),
                    node_type: 'for_range',
                    variable: block.getFieldValue('VAR') || 'i',
                    from: expressionFrom(block.getInputTargetBlock('FROM')),
                    to: expressionFrom(block.getInputTargetBlock('TO')),
                    by: expressionFrom(block.getInputTargetBlock('BY')),
                    body: sequenceFrom(block.getInputTargetBlock('DO'), metadata),
                };
            }
            return {
                id: blockId(block),
                node_type: 'for_each',
                variable: block.getFieldValue('VAR') || 'item',
                collection: expressionFrom(block.getInputTargetBlock('LIST')),
                body: sequenceFrom(block.getInputTargetBlock('DO'), metadata),
            };
        }

        function convertFlowStatement(block) {
            const flow = (block.getFieldValue('FLOW') || 'BREAK').toLowerCase();
            return {
                id: blockId(block),
                node_type: 'flow',
                flow,
            };
        }

        Generator.workspaceToDocument = function(workspace) {
            const metadata = {};
            const sequence = [];
            const topBlocks = workspace.getTopBlocks(true);
            topBlocks.forEach(block => {
                sequence.push(...sequenceFrom(block, metadata));
            });

            return {
                version: '1.0',
                metadata,
                sequence,
            };
        };

        Blockly.RobotIR = Generator;
    }

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
        setTimeout(init, 0);
    } else {
        document.addEventListener('DOMContentLoaded', init);
    }
})(window);
