// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @dev Interface for ERC-8004: Autonomous Agent Identity & Wallet
 * Allows an agent's on-chain identity to execute arbitrary transactions.
 */
interface IERC8004 {
    function executeCall(address to, uint256 value, bytes calldata data) external payable returns (bytes memory);
    function agentSigner() external view returns (address);
}

/**
 * @title ERC8004AgentIdentity
 * @dev Combines Soulbound Identity (ERC-721) with Smart Wallet functionality.
 */
contract ERC8004AgentIdentity is ERC721, Ownable, IERC8004 {
    uint256 private _nextTokenId = 1;
    mapping(uint256 => string) private _tokenURIs;
    
    // Maps Token ID to the specific Agent Signer Key that controls it
    mapping(uint256 => address) public tokenToAgentSigner;
    // Maps an Agent Signer Key to its Token ID
    mapping(address => uint256) public agentSignerToToken;

    event AgentIdentityMinted(address indexed agentSigner, uint256 indexed tokenId, string uri);
    event Executed(address indexed to, uint256 value, bytes data);

    constructor(address initialOwner) ERC721("Agentic Identity", "AGNT") Ownable(initialOwner) {}

    /**
     * @dev Mint a new identity. The agentSigner becomes the "brain" of this smart wallet.
     */
    function mintIdentity(address _agentSigner, string memory reputationURI) public onlyOwner {
        require(agentSignerToToken[_agentSigner] == 0, "Signer already controls an identity");
        
        uint256 tokenId = _nextTokenId++;
        _safeMint(_agentSigner, tokenId); // Initially minted to the signer address
        
        _tokenURIs[tokenId] = reputationURI;
        tokenToAgentSigner[tokenId] = _agentSigner;
        agentSignerToToken[_agentSigner] = tokenId;
        
        emit AgentIdentityMinted(_agentSigner, tokenId, reputationURI);
    }

    /**
     * @dev ERC-8004 Execute: The agent signer can use this contract as a wallet.
     */
    function executeCall(address to, uint256 value, bytes calldata data) external payable override returns (bytes memory) {
        require(agentSignerToToken[msg.sender] != 0, "Caller is not an authorized agent signer");
        require(ownerOf(agentSignerToToken[msg.sender]) == msg.sender, "Caller does not own the identity token");
        
        (bool success, bytes memory result) = to.call{value: value}(data);
        require(success, "Underlying execution failed");
        
        emit Executed(to, value, data);
        return result;
    }

    function agentSigner() external view override returns (address) {
        return tokenToAgentSigner[1]; // Simplified for demo. In a real system, each proxy has 1 signer.
    }

    function tokenURI(uint256 tokenId) public view virtual override returns (string memory) {
        ownerOf(tokenId);
        return _tokenURIs[tokenId];
    }

    // --- SOULBOUND LOGIC ---
    function transferFrom(address from, address to, uint256 tokenId) public virtual override {
        revert("ERC-8004: Agent Identities are non-transferable");
    }

    function safeTransferFrom(address from, address to, uint256 tokenId, bytes memory data) public virtual override {
        revert("ERC-8004: Agent Identities are non-transferable");
    }

    // Allow contract to receive ETH
    receive() external payable {}
}
