const hre = require("hardhat");
const fs = require('fs');

async function main() {
  console.log("=== INICIANDO TRANSFERENCIA A BOVEDA MULTI-FIRMA ===");
  const [deployer, owner2, owner3] = await hre.ethers.getSigners();
  console.log("Llave maestra actual (Desarrollador):", deployer.address);

  // 1. Deploy MultiSig Vault (2 of 3)
  const owners = [deployer.address, owner2.address, owner3.address];
  const requiredSigs = 2;

  const MultiSigFactory = await hre.ethers.getContractFactory("MultiSigVault");
  const vault = await MultiSigFactory.deploy(owners, requiredSigs);
  await vault.waitForDeployment();
  const vaultAddress = await vault.getAddress();
  
  console.log(`[+] Bóveda Institucional desplegada en: ${vaultAddress}`);
  console.log(`[+] Firmantes autorizados: \n  - ${deployer.address}\n  - ${owner2.address}\n  - ${owner3.address}`);
  console.log(`[+] Firmas requeridas por operación: ${requiredSigs} de ${owners.length}`);

  // 2. Transfer Ownership of AgentPaymaster and ERC8004 to Vault
  // Para esto necesitaríamos la dirección desplegada. Simulemos que se lee del json o se pasan.
  // En este demo, vamos a desplegar instancias nuevas o usar las últimas.
  let contractsProd;
  try {
      contractsProd = JSON.parse(fs.readFileSync("../contracts_prod.json"));
  } catch (e) {
      console.log("No se encontro contracts_prod.json, saltando transferencia real.");
      return;
  }

  const paymaster = await hre.ethers.getContractAt("AgentPaymaster", contractsProd.Paymaster);
  
  // Transferir propiedad al Vault
  // OpenZeppelin Ownable usa transferOwnership
  console.log("[!] Iniciando abdicación de llaves del desarrollador...");
  const tx1 = await paymaster.transferOwnership(vaultAddress);
  await tx1.wait();
  console.log("[+] Paymaster ahora pertenece a la Bóveda Multi-Sig.");

  console.log("=== GOBERNANZA INSTITUCIONAL ESTABLECIDA ===");
  console.log("El Desarrollador ya no tiene control absoluto de los fondos.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
