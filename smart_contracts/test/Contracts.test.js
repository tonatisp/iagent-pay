const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("iAgentPay Smart Contracts", function () {
  let owner;
  let agent;
  let enterprise;
  let user;
  
  let AgentIdentity;
  let identityContract;
  
  let AgentPaymaster;
  let paymasterContract;
  
  let ERC8004Identity;
  let erc8004Contract;

  beforeEach(async function () {
    [owner, agent, enterprise, user] = await ethers.getSigners();

    // Deploy Identity
    AgentIdentity = await ethers.getContractFactory("AgentIdentity");
    identityContract = await AgentIdentity.deploy(owner.address);

    // Deploy Paymaster
    AgentPaymaster = await ethers.getContractFactory("AgentPaymaster");
    paymasterContract = await AgentPaymaster.deploy(owner.address);

    // Deploy ERC8004 Identity
    ERC8004Identity = await ethers.getContractFactory("ERC8004AgentIdentity");
    erc8004Contract = await ERC8004Identity.deploy(owner.address);
  });

  describe("AgentIdentity (Soulbound KYA)", function () {
    it("Should mint an identity for an agent", async function () {
      await identityContract.mintIdentity(agent.address, "ipfs://reputation");
      expect(await identityContract.ownerOf(1)).to.equal(agent.address);
      expect(await identityContract.hasIdentity(agent.address)).to.equal(true);
      expect(await identityContract.tokenURI(1)).to.equal("ipfs://reputation");
    });

    it("Should prevent transferring the identity (Soulbound)", async function () {
      await identityContract.mintIdentity(agent.address, "ipfs://reputation");
      await expect(
        identityContract.connect(agent).transferFrom(agent.address, enterprise.address, 1)
      ).to.be.revertedWith("Soulbound: Identity tokens cannot be transferred");
      
      await expect(
        identityContract.connect(agent)["safeTransferFrom(address,address,uint256)"](agent.address, enterprise.address, 1)
      ).to.be.revertedWith("Soulbound: Identity tokens cannot be transferred");
    });
  });

  describe("AgentPaymaster (Gasless Sponsorship)", function () {
    it("Should allow enterprise to deposit and authorize an agent", async function () {
      await paymasterContract.connect(enterprise).deposit({ value: ethers.parseEther("1.0") });
      expect(await paymasterContract.sponsorBalances(enterprise.address)).to.equal(ethers.parseEther("1.0"));

      await paymasterContract.connect(enterprise).authorizeAgent(agent.address);
      
      const isAuth = await paymasterContract.validatePaymasterUserOp(enterprise.address, agent.address, 100000);
      expect(isAuth).to.equal(true);
    });

    it("Should reject unauthorized agents", async function () {
      await expect(
        paymasterContract.validatePaymasterUserOp(enterprise.address, agent.address, 100000)
      ).to.be.revertedWith("Agent not authorized by sponsor");
    });
  });

  describe("ERC8004AgentIdentity (Wallet Identity)", function () {
    it("Should mint an ERC8004 identity", async function () {
      await erc8004Contract.mintIdentity(agent.address, "ipfs://reputation");
      expect(await erc8004Contract.ownerOf(1)).to.equal(agent.address);
      expect(await erc8004Contract.tokenURI(1)).to.equal("ipfs://reputation");
      expect(await erc8004Contract.agentSigner()).to.equal(agent.address);
    });

    it("Should prevent transferring the ERC8004 identity", async function () {
      await erc8004Contract.mintIdentity(agent.address, "ipfs://reputation");
      await expect(
        erc8004Contract.connect(agent).transferFrom(agent.address, enterprise.address, 1)
      ).to.be.revertedWith("ERC-8004: Agent Identities are non-transferable");
      
      await expect(
        erc8004Contract.connect(agent)["safeTransferFrom(address,address,uint256)"](agent.address, enterprise.address, 1)
      ).to.be.revertedWith("ERC-8004: Agent Identities are non-transferable");
    });
    
    it("Should allow agent to executeCall with funds", async function () {
      await erc8004Contract.mintIdentity(agent.address, "ipfs://reputation");
      
      // Fund the contract
      await owner.sendTransaction({ to: await erc8004Contract.getAddress(), value: ethers.parseEther("1.0") });
      
      // Agent calls `executeCall` to send ETH to user
      const initBalance = await ethers.provider.getBalance(user.address);
      await erc8004Contract.connect(agent).executeCall(user.address, ethers.parseEther("0.5"), "0x");
      const finalBalance = await ethers.provider.getBalance(user.address);
      
      expect(finalBalance - initBalance).to.equal(ethers.parseEther("0.5"));
    });

    it("Should revert if non-agent tries to executeCall", async function () {
      await erc8004Contract.mintIdentity(agent.address, "ipfs://reputation");
      await expect(
        erc8004Contract.connect(user).executeCall(user.address, 0, "0x")
      ).to.be.revertedWith("Caller is not an authorized agent signer");
    });
  });

  describe("Fuzzing & Invariant Testing (Enterprise Grade)", function () {
    it("Fuzzing: Should maintain invariants under random high-volume operations", async function () {
      const wallets = Array.from({ length: 50 }).map(() => ethers.Wallet.createRandom().connect(ethers.provider));
      
      // 1. Invariant: Only owner can mint
      const randomWallet = wallets[Math.floor(Math.random() * wallets.length)];
      await expect(
        erc8004Contract.connect(randomWallet).mintIdentity(randomWallet.address, "ipfs://fuzz")
      ).to.be.reverted; // Ownable error
      
      // 2. Fuzz Minting from Owner
      await erc8004Contract.connect(owner).mintIdentity(agent.address, "ipfs://fuzz_agent");
      const tokenId = await erc8004Contract.agentSignerToToken(agent.address);
      
      // 3. Fuzz executeCall with 100 randomized inputs
      await owner.sendTransaction({ to: await erc8004Contract.getAddress(), value: ethers.parseEther("10.0") });
      
      for(let i = 0; i < 50; i++) {
        const randomTarget = wallets[i];
        const randomAmount = ethers.parseEther((Math.random() * 0.1).toFixed(4));
        
        const initBal = await ethers.provider.getBalance(randomTarget.address);
        await erc8004Contract.connect(agent).executeCall(randomTarget.address, randomAmount, "0x");
        const finalBal = await ethers.provider.getBalance(randomTarget.address);
        
        expect(finalBal - initBal).to.equal(randomAmount);
      }

      // 4. Invariant: Soulbound Non-Transferability across 50 random attempts
      for(let i = 0; i < 10; i++) {
        const randomTarget = wallets[Math.floor(Math.random() * wallets.length)];
        await expect(
          erc8004Contract.connect(agent).transferFrom(agent.address, randomTarget.address, tokenId)
        ).to.be.revertedWith("ERC-8004: Agent Identities are non-transferable");
      }
    });
  });
});
