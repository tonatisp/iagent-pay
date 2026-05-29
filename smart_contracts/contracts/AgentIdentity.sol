// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title AgentIdentity
 * @dev Soulbound Token (SBT) representing an Autonomous AI Agent's On-Chain Reputation (KYA).
 * Soulbound means it cannot be transferred once minted.
 */
contract AgentIdentity is ERC721, Ownable {
    uint256 private _nextTokenId = 1;
    mapping(uint256 => string) private _tokenURIs;
    mapping(address => bool) public hasIdentity;

    event AgentIdentityMinted(address indexed agent, uint256 indexed tokenId, string uri);

    constructor(address initialOwner) ERC721("iAgentPay KYA Identity", "iKYA") Ownable(initialOwner) {}

    /**
     * @dev Mints a new Soulbound Identity for an agent.
     * Can only be called by the platform owner (or authorized oracle) to ensure reputation is verified.
     */
    function mintIdentity(address agent, string memory reputationURI) public onlyOwner {
        require(!hasIdentity[agent], "Agent already has an identity SBT");
        
        uint256 tokenId = _nextTokenId++;
        _safeMint(agent, tokenId);
        _tokenURIs[tokenId] = reputationURI;
        hasIdentity[agent] = true;
        
        emit AgentIdentityMinted(agent, tokenId, reputationURI);
    }

    function tokenURI(uint256 tokenId) public view virtual override returns (string memory) {
        ownerOf(tokenId); // Reverts if token doesn't exist
        return _tokenURIs[tokenId];
    }

    // --- SOULBOUND LOGIC ---
    // Overriding transfer functions to make the token non-transferable

    function transferFrom(address from, address to, uint256 tokenId) public virtual override {
        revert("Soulbound: Identity tokens cannot be transferred");
    }

    function safeTransferFrom(address from, address to, uint256 tokenId, bytes memory data) public virtual override {
        revert("Soulbound: Identity tokens cannot be transferred");
    }
}
