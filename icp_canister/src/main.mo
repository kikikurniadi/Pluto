import Debug "mo:base/Debug";

// Minimal canister: store a PEM-encoded public key for provenance verification.
persistent actor AnchorRegistry {
  stable var pubkey : Text = "";

  public func set_pubkey(pem: Text) : async Text {
    pubkey := pem;
    Debug.print("Stored pubkey");
    return "ok";
  };

  public query func get_pubkey() : async Text {
    return pubkey;
  };
};
