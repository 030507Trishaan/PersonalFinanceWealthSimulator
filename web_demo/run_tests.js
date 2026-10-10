const funcs = require('./app.js');
global.calculateProjection = funcs.calculateProjection;
global.runScenarioComparison = funcs.runScenarioComparison;
global.calculateGoalPlanner = funcs.calculateGoalPlanner;
global.formatINR = funcs.formatINR;

const testModule = require('./calculation-tests.js');
const result = testModule.runAllCalculationTests();
process.exit(result ? 0 : 1);
