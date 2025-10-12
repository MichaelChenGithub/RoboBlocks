(function(global) {
    function init() {
        const Blockly = global.Blockly;
        if (!Blockly || !Blockly.Python) {
            console.error('Blockly Python generator is not available.');
            return;
        }

        const python = Blockly.Python;

        python.addReservedWords('new_robot,cv_model');

        function isWithinMain(block) {
            let current = block;
            while (current) {
                if (current.type === 'main_entry') {
                    return true;
                }
                current = current.getParent();
            }
            return false;
        }

        function ensureRobotRuntime() {
            python.definitions_ = python.definitions_ || Object.create(null);
            if (!python.definitions_['import_robot_module']) {
                python.definitions_['import_robot_module'] = 'from tools.robot import Robot';
            }
            if (!python.definitions_['robot_instance']) {
                python.definitions_['robot_instance'] = 'new_robot = Robot()';
            }
        }

        function ensureCvModelRuntime() {
            python.definitions_ = python.definitions_ || Object.create(null);
            if (!python.definitions_['import_cv_model']) {
                python.definitions_['import_cv_model'] = 'from tools.vision import CVModel';
            }
            if (!python.definitions_['cv_model_instance']) {
                python.definitions_['cv_model_instance'] = 'cv_model = CVModel()';
            }
        }

        function statement(block, methodName, argsBuilder, target) {
            if (!block || !block.getParent()) {
                return '';
            }
            if (!block || !isWithinMain(block)) {
                return '';
            }
            const args = argsBuilder ? argsBuilder(block) : '';
            const receiver = target || 'new_robot';
            if (receiver === 'new_robot') {
                ensureRobotRuntime();
            } else if (receiver === 'cv_model') {
                ensureCvModelRuntime();
            }
            return `${receiver}.${methodName}(${args})\n`;
        }

        function numberField(block, field, fallback) {
            return Number(block.getFieldValue(field) || fallback || 0);
        }

        function textField(block, field, fallback) {
            const value = block.getFieldValue(field);
            return JSON.stringify(value ?? fallback ?? '');
        }

        python.forBlock['main_entry'] = function(block) {
            const branch = python.statementToCode(block, 'DO');
            const body = branch || `${python.INDENT}pass\n`;
            const code = `def main():\n${body}\nif __name__ == "__main__":\n    main()\n`;
            return code;
        };

        python.forBlock['connect_robot'] = function(block) {
            if (!block.getParent()) {
                return '';
            }
            if (!isWithinMain(block)) {
                return '';
            }

            const ip = textField(block, 'IP', '192.168.0.10');
            const port = numberField(block, 'PORT', 60008);
            const timeout = numberField(block, 'TIMEOUT', 5000);
            const brand = block.getFieldValue('ROBOT_BRAND') || 'default';
            const lines = [
                `new_robot.brand = ${JSON.stringify(brand)}\n`,
                statement(block, 'action.connect_robot', () => `${ip}, port=${port}, timeout_ms=${timeout}`)
            ];
            return lines.join('');
        };

        python.forBlock['disconnect_robot'] = function(block) {
            return statement(block, 'action.disconnect');
        };

        python.forBlock['power_on_servo'] = function(block) {
            return statement(block, 'action.power_on_servo');
        };

        python.forBlock['power_off_servo'] = function(block) {
            return statement(block, 'action.power_off_servo');
        };

        python.forBlock['set_speed'] = function(block) {
            const speed = numberField(block, 'PERCENTAGE', 50);
            return statement(block, 'motion.set_speed', () => `${speed}`);
        };

        python.forBlock['set_acceleration'] = function(block) {
            const accel = numberField(block, 'PERCENTAGE', 50);
            return statement(block, 'motion.set_acceleration', () => `${accel}`);
        };

        python.forBlock['move_to'] = function(block) {
            const x = numberField(block, 'X', 0);
            const y = numberField(block, 'Y', 0);
            const z = numberField(block, 'Z', 0);
            const speed = numberField(block, 'SPEED', 50);
            return statement(block, 'motion.move_to', () => `${x}, ${y}, ${z}, speed=${speed}`);
        };

        python.forBlock['move_joint'] = function(block) {
            const joints = ['J1','J2','J3','J4','J5','J6'].map(name => numberField(block, name, 0));
            const speed = numberField(block, 'SPEED', 50);
            return statement(block, 'motion.move_joint', () => `${joints.join(', ')}, speed=${speed}`);
        };

        python.forBlock['move_linear'] = function(block) {
            const axes = ['X','Y','Z','RX','RY','RZ'].map(name => numberField(block, name, 0));
            const speed = numberField(block, 'SPEED', 50);
            return statement(block, 'motion.move_linear', () => `${axes.join(', ')}, speed=${speed}`);
        };

        python.forBlock['move_circular'] = function(block) {
            const via = ['VX','VY','VZ','VRX','VRY','VRZ'].map(name => numberField(block, name, 0));
            const end = ['EX','EY','EZ','ERX','ERY','ERZ'].map(name => numberField(block, name, 0));
            return statement(block, 'motion.move_circular', () => `via=(${via.join(', ')}), end=(${end.join(', ')})`);
        };

        python.forBlock['stop_motion'] = function(block) {
            const stopType = block.getFieldValue('STOP_TYPE');
            if (stopType) {
                return statement(block, 'motion.stop', () => `${JSON.stringify(stopType)}`);
            }
            return statement(block, 'motion.stop');
        };

        python.forBlock['wait_for_move_finish'] = function(block) {
            const timeout = numberField(block, 'TIMEOUT', 0);
            if (timeout) {
                return statement(block, 'motion.wait_for_finish', () => `timeout_ms=${timeout}`);
            }
            return statement(block, 'motion.wait_for_finish');
        };

        python.forBlock['set_tool_coordinate'] = function(block) {
            const coords = ['TX','TY','TZ','TRX','TRY','TRZ'].map(name => numberField(block, name, 0));
            return statement(block, 'frames.set_tool', () => `${coords.join(', ')}`);
        };

        python.forBlock['set_user_coordinate'] = function(block) {
            const coords = ['UX','UY','UZ','URX','URY','URZ'].map(name => numberField(block, name, 0));
            return statement(block, 'frames.set_user', () => `${coords.join(', ')}`);
        };

        python.forBlock['grab'] = function(block) {
            return statement(block, 'gripper.grab');
        };

        python.forBlock['release'] = function(block) {
            return statement(block, 'gripper.release');
        };

        python.forBlock['print_numbers'] = function(block) {
            return statement(block, 'debug.print_numbers');
        };

        python.forBlock['get_current_joint_position'] = function(block) {
            const store = block.getFieldValue('STORE');
            const call = statement(block, 'status.joint_position');
            const callLine = call.trim();
            if (!callLine) {
                return '';
            }
            if (store) {
                return `${store} = ${callLine}\n`;
            }
            return `${callLine}\n`;
        };

        python.forBlock['get_current_cartesian_position'] = function(block) {
            const store = block.getFieldValue('STORE');
            const call = statement(block, 'status.cartesian_position');
            const callLine = call.trim();
            if (!callLine) {
                return '';
            }
            if (store) {
                return `${store} = ${callLine}\n`;
            }
            return `${callLine}\n`;
        };

        python.forBlock['get_robot_status'] = function(block) {
            const store = block.getFieldValue('STORE');
            const call = statement(block, 'status.snapshot');
            const callLine = call.trim();
            if (!callLine) {
                return '';
            }
            if (store) {
                return `${store} = ${callLine}\n`;
            }
            return `${callLine}\n`;
        };

        python.forBlock['set_digital_output'] = function(block) {
            const port = numberField(block, 'PORT', 0);
            const value = block.getFieldValue('VALUE') === 'TRUE' ? 'True' : 'False';
            return statement(block, 'io.set_output', () => `${port}, ${value}`);
        };

        python.forBlock['get_digital_input'] = function(block) {
            const port = numberField(block, 'PORT', 0);
            const store = block.getFieldValue('STORE');
            const call = statement(block, 'io.get_input', () => `${port}`);
            const callLine = call.trim();
            if (!callLine) {
                return '';
            }
            if (store) {
                return `${store} = ${callLine}\n`;
            }
            return `${callLine}\n`;
        };

        python.forBlock['create_model'] = function(block) {
            return statement(block, 'create_model', null, 'cv_model');
        };

        python.forBlock['set_hyperparams'] = function(block) {
            const a = numberField(block, 'PARAM_A', 0);
            const b = numberField(block, 'PARAM_B', 0);
            const c = numberField(block, 'PARAM_C', 0);
            return statement(block, 'set_hyperparams', () => `${a}, ${b}, ${c}`, 'cv_model');
        };
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})(window);
