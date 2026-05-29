// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title AgentPaymaster
 * @dev A simplified gas sponsorship vault for AI Agents. 
 * Enterprises deposit ETH here to sponsor their fleet of agents.
 * Full EIP-4337 integration requires linking to the EntryPoint contract.
 */
contract AgentPaymaster is Ownable {
    mapping(address => uint256) public sponsorBalances;
    mapping(address => mapping(address => bool)) public authorizedAgents; // sponsor -> agent -> isAuthorized

    event Deposited(address indexed sponsor, uint256 amount);
    event AgentAuthorized(address indexed sponsor, address indexed agent);
    event AgentRevoked(address indexed sponsor, address indexed agent);

    constructor(address initialOwner) Ownable(initialOwner) {}

    // 1. Enterprise deposits ETH to sponsor their agents
    function deposit() public payable {
        require(msg.value > 0, "Must deposit ETH");
        sponsorBalances[msg.sender] += msg.value;
        emit Deposited(msg.sender, msg.value);
    }

    // 2. Enterprise authorizes a specific AI Agent address to use their gas
    function authorizeAgent(address agent) public {
        authorizedAgents[msg.sender][agent] = true;
        emit AgentAuthorized(msg.sender, agent);
    }

    // 3. Enterprise revokes access
    function revokeAgent(address agent) public {
        authorizedAgents[msg.sender][agent] = false;
        emit AgentRevoked(msg.sender, agent);
    }

    // 4. EIP-4337 Validation (Mock function for Phase 7 MVP)
    // In production, the EntryPoint contract calls validatePaymasterUserOp
    function validatePaymasterUserOp(address sponsor, address agent, uint256 requiredGas) public view returns (bool) {
        require(authorizedAgents[sponsor][agent], "Agent not authorized by sponsor");
        require(sponsorBalances[sponsor] >= requiredGas, "Sponsor has insufficient gas balance");
        return true;
    }
}
