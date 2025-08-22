export const idlFactory = ({ IDL }) => {
  return IDL.Service({
    'get_pubkey' : IDL.Func([], [IDL.Text], ['query']),
    'set_pubkey' : IDL.Func([IDL.Text], [IDL.Text], []),
  });
};
export const init = ({ IDL }) => { return []; };
