const hre = require("hardhat");
const fs = require('fs');

async function main() {
  console.log("Iniciando despliegue en Producción...");
  const [deployer] = await hre.ethers.getSigners();
  console.log("Desplegando contratos con la cuenta:", deployer.address);

  // Deploy ERC8004
  const ERC8004Factory = await hre.ethers.getContractFactory("ERC8004AgentIdentity");
  const erc8004 = await ERC8004Factory.deploy(deployer.address);
  await erc8004.waitForDeployment();
  const erc8004Address = await erc8004.getAddress();
  console.log("ERC8004AgentIdentity desplegado en:", erc8004Address);

  // Deploy Paymaster
  const PaymasterFactory = await hre.ethers.getContractFactory("AgentPaymaster");
  const paymaster = await PaymasterFactory.deploy(erc8004Address);
  await paymaster.waitForDeployment();
  const paymasterAddress = await paymaster.getAddress();
  console.log("AgentPaymaster desplegado en:", paymasterAddress);

  // Save addresses to JSON for backend
  const addresses = {
    ERC8004: erc8004Address,
    Paymaster: paymasterAddress,
    Network: hre.network.name
  };
  fs.writeFileSync("../contracts_prod.json", JSON.stringify(addresses, null, 2));
  console.log("Direcciones guardadas en contracts_prod.json");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
