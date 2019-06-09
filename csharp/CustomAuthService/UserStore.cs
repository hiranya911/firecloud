using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace CustomAuthService
{
    /// <summary>
    /// Represents an external database or API where the user information is stored. This can
    /// be a LDAP server, Active Directory instance or some other user information store.
    /// </summary>
    public class UserStore
    {
        private static readonly IReadOnlyDictionary<string, User> Users =
            new Dictionary<string, User>()
            {
                {
                    "alice:password",
                    new User("alice")
                },
                {
                    "bob:secret",
                    new User("bob")
                },
            };

        public Task<User> LoginAsync(LoginRequest request)
        {
            if (string.IsNullOrEmpty(request.Username))
            {
                throw new Exception("Username not specified");
            }

            var key = $"{request.Username}:{request.Password ?? string.Empty}";
            User user;
            if (!Users.TryGetValue(key, out user))
            {
                throw new Exception("Incorrect username or password");
            }

            return Task.FromResult(user);
        }
    }

    public sealed class User
    {
        internal User(string uid, IDictionary<string, object> claims = null)
        {
            if (string.IsNullOrEmpty(uid))
            {
                throw new ArgumentException("uid must not be null or empty");
            }
            this.Uid = uid;
            this.Claims = claims;
        }

        public string Uid { get; private set; }

        public IDictionary<string, object> Claims { get; private set; }
    }
}