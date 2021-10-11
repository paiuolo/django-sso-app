pragma solidity ^0.5.10;

import "../node_modules/openzeppelin-solidity/contracts/token/ERC721/IERC721.sol";
import "../node_modules/openzeppelin-solidity/contracts/token/ERC721/IERC721Receiver.sol";
import "../node_modules/openzeppelin-solidity/contracts/introspection/ERC165.sol";
import "../node_modules/openzeppelin-solidity/contracts/math/SafeMath.sol";

contract DjangoSsoAppProfileContract is IERC721, ERC165 {

    // Use Open Zeppelin's SafeMath library to perform arithmetic operations safely.
    using SafeMath for uint256;

    /*
        A DjangoSsoAppProfileContract has only **len(<profile_fields>)** parts that can change according to its DNA.
        When we generate DNA, we get a 10 digit long number, and each pair corresponds to a specific profile field (hashed).

        E.g. DNA 5142446803 - 51_Basis/42_Cheeses/44_Meats/68_Spices/03_Vegetables
    */
    uint constant dnaDigits = 10;
    uint constant dnaModulus = 10 ** dnaDigits;

    // Equals to `bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"))`
    // which can be also obtained as `IERC721Receiver(0).onERC721Received.selector`
    bytes4 private constant _ERC721_RECEIVED = 0x150b7a02;

    struct Profile {
        string name;
        uint dna;
    }

    Profile[] public profiles;

    // Mapping from owner to id of Profile
    mapping (uint => address) public profileToOwner;

    // Mapping from owner to number of owned token
    mapping (address => uint) public ownerProfileCount;

    // Mapping from token ID to approved address
    mapping (uint => address) profileApprovals;

    // Mapping from owner to operator approvals
    mapping (address => mapping (address => bool)) private operatorApprovals;

    // Create random Profile from string (name) and DNA
    function _createProfile(string memory _name, uint _dna)
        internal
        isUnique(_name, _dna)
    {
        // Add Profile to array and get id
        uint id = SafeMath.sub(profiles.push(Profile(_name, _dna)), 1);
        // Map owner to id of Profile
        assert(profileToOwner[id] == address(0));
        profileToOwner[id] = msg.sender;
        ownerProfileCount[msg.sender] = SafeMath.add(ownerProfileCount[msg.sender], 1);
    }

    // Creates random Profile from string (name)
    function createRandomProfile(string memory _name)
        public
    {
        uint randDna = generateRandomDna(_name, msg.sender);
        _createProfile(_name, randDna);
    }

    // Generate random DNA from string (name) and address of the owner (creator)
    function generateRandomDna(string memory _str, address _owner)
        public
        pure
        returns(uint)
    {
        // Generate random uint from string (name) + address (owner)
        uint rand = uint(keccak256(abi.encodePacked(_str))) + uint(_owner);
        rand = rand % dnaModulus;
        return rand;
    }

    // Returns array of Profiles found by owner
    function getProfilesByOwner(address _owner)
        public
        view
        returns(uint[] memory)
    {
        uint[] memory result = new uint[](ownerProfileCount[_owner]);
        uint counter = 0;
        for (uint i = 0; i < profiles.length; i++) {
            if (profileToOwner[i] == _owner) {
                result[counter] = i;
                counter++;
            }
        }
        return result;
    }

    // Transfer Profile to other wallet (internal function)
    function transferFrom(address _from, address _to, uint256 _profileId)
        public
    {
        require(_from != address(0) && _to != address(0));
        require(_exists(_profileId));
        require(_from != _to);
        require(_isApprovedOrOwner(msg.sender, _profileId));
        ownerProfileCount[_to] = SafeMath.add(ownerProfileCount[_to], 1);
        ownerProfileCount[_from] = SafeMath.sub(ownerProfileCount[_from], 1);
        profileToOwner[_profileId] = _to;
        emit Transfer(_from, _to, _profileId);
        _clearApproval(_to, _profileId);
    }

    /**
     * Safely transfers the ownership of a given token ID to another address
     * If the target address is a contract, it must implement `onERC721Received`,
     * which is called upon a safe transfer, and return the magic value
     * `bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"))`; otherwise,
     * the transfer is reverted.
    */
    function safeTransferFrom(address from, address to, uint256 profileId)
        public
    {
        // solium-disable-next-line arg-overflow
        this.safeTransferFrom(from, to, profileId, "");
    }

    /**
     * Safely transfers the ownership of a given token ID to another address
     * If the target address is a contract, it must implement `onERC721Received`,
     * which is called upon a safe transfer, and return the magic value
     * `bytes4(keccak256("onERC721Received(address,address,uint256,bytes)"))`; otherwise,
     */
    function safeTransferFrom(address from, address to, uint256 profileId, bytes memory _data)
        public
    {
        this.transferFrom(from, to, profileId);
        // solium-disable-next-line arg-overflow
        require(_checkOnERC721Received(from, to, profileId, _data));
    }

    /**
     * Internal function to invoke `onERC721Received` on a target address
     * The call is not executed if the target address is not a contract
     */
    function _checkOnERC721Received(address from, address to, uint256 profileId, bytes memory _data)
        internal
        returns(bool)
    {
        if (!isContract(to)) {
            return true;
        }

        bytes4 retval = IERC721Receiver(to).onERC721Received(msg.sender, from, profileId, _data);
        return (retval == _ERC721_RECEIVED);
    }

    // Burn Profile - destroys Token completely
    function burn(uint256 _profileId)
        external
    {
        require(msg.sender != address(0));
        require(_exists(_profileId));
        require(_isApprovedOrOwner(msg.sender, _profileId));
        ownerProfileCount[msg.sender] = SafeMath.sub(ownerProfileCount[msg.sender], 1);
        profileToOwner[_profileId] = address(0);
    }

    // Returns count of Profiles by address
    function balanceOf(address _owner)
        public
        view
        returns(uint256 _balance)
    {
        return ownerProfileCount[_owner];
    }

    // Returns owner of the Profile found by id
    function ownerOf(uint256 _profileId)
        public
        view
        returns(address _owner)
    {
        address owner = profileToOwner[_profileId];
        require(owner != address(0));
        return owner;
    }

    // Approve other wallet to transfer ownership of Profile
    function approve(address _to, uint256 _profileId)
        public
    {
        require(msg.sender == profileToOwner[_profileId]);
        profileApprovals[_profileId] = _to;
        emit Approval(msg.sender, _to, _profileId);
    }

    // Return approved address for specific Profile
    function getApproved(uint256 profileId)
        public
        view
        returns(address operator)
    {
        require(_exists(profileId));
        return profileApprovals[profileId];
    }

    /**
     * Private function to clear current approval of a given token ID
     * Reverts if the given address is not indeed the owner of the token
     */
    function _clearApproval(address owner, uint256 profileId) private {
        require(profileToOwner[profileId] == owner);
        require(_exists(profileId));
        if (profileApprovals[profileId] != address(0)) {
            profileApprovals[profileId] = address(0);
        }
    }

    /*
     * Sets or unsets the approval of a given operator
     * An operator is allowed to transfer all tokens of the sender on their behalf
     */
    function setApprovalForAll(address to, bool approved)
        public
    {
        require(to != msg.sender);
        operatorApprovals[msg.sender][to] = approved;
        emit ApprovalForAll(msg.sender, to, approved);
    }

    // Tells whether an operator is approved by a given owner
    function isApprovedForAll(address owner, address operator)
        public
        view
        returns(bool)
    {
        return operatorApprovals[owner][operator];
    }

    // Take ownership of Profile - only for approved users
    function takeOwnership(uint256 _profileId)
        public
    {
        require(_isApprovedOrOwner(msg.sender, _profileId));
        address owner = this.ownerOf(_profileId);
        this.transferFrom(owner, msg.sender, _profileId);
    }

    // Check if Profile exists
    function _exists(uint256 profileId)
        internal
        view
        returns(bool)
    {
        address owner = profileToOwner[profileId];
        return owner != address(0);
    }

    function _isApprovedOrOwner(address spender, uint256 profileId)
        internal
        view
        returns(bool)
    {
        address owner = profileToOwner[profileId];
        // Disable solium check because of
        // https://github.com/duaraghav8/Solium/issues/175
        // solium-disable-next-line operator-whitespace
        return (spender == owner || this.getApproved(profileId) == spender || this.isApprovedForAll(owner, spender));
    }

    // Check if Profile is unique and doesn't exist yet
    modifier isUnique(string memory _name, uint256 _dna) {
        bool result = true;
        for(uint i = 0; i < profiles.length; i++) {
            if(keccak256(abi.encodePacked(profiles[i].name)) == keccak256(abi.encodePacked(_name)) && profiles[i].dna == _dna) {
                result = false;
            }
        }
        require(result, "Profile with such name already exists.");
        _;
    }

    // Returns whether the target address is a contract
    function isContract(address account)
        internal
        view
        returns(bool)
    {
        uint256 size;
        // XXX Currently there is no better way to check if there is a contract in an address
        // than to check the size of the code at that address.
        // See https://ethereum.stackexchange.com/a/14016/36603
        // for more details about how this works.
        // TODO Check this again before the Serenity release, because all addresses will be
        // contracts then.
        // solium-disable-next-line security/no-inline-assembly
        assembly { size := extcodesize(account) }
        return size > 0;
    }
}
