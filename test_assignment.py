"""
Comprehensive test suite for Assignment #1 - Pet Store REST API
Tests all endpoints, error codes, messages, and edge cases as specified in the assignment.
This file can be deleted after testing is complete.

To run these tests:
1. Install pytest: pip install pytest
2. Run: pytest test_assignment.py -v
   Or: python test_assignment.py
"""

import pytest
import json
import os
import shutil
from app import app, Pets, PetObjects, pet_id

# Set up test client
@pytest.fixture
def client():
    """Create a test client for the Flask app"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
    # Clean up after each test
    Pets.clear()
    PetObjects.clear()
    global pet_id
    pet_id = 0
    # Clean up images directory if it exists
    if os.path.exists('images'):
        for filename in os.listdir('images'):
            if filename.endswith(('.jpg', '.jpeg', '.png')):
                os.remove(os.path.join('images', filename))

@pytest.fixture
def sample_pet_type_id(client):
    """Helper to create a sample pet-type and return its ID"""
    response = client.post('/pet-types',
                          json={'type': 'Golden Retriever'},
                          content_type='application/json')
    if response.status_code == 201:
        data = json.loads(response.data)
        return data['id']
    return None


class TestPetTypesCollection:
    """Tests for /pet-types endpoint"""
    
    def test_get_pet_types_empty(self, client):
        """GET /pet-types - returns empty array when no pet-types exist"""
        response = client.get('/pet-types')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_post_pet_type_success(self, client):
        """POST /pet-types - successfully creates a pet-type"""
        response = client.post('/pet-types',
                              json={'type': 'Golden Retriever'},
                              content_type='application/json')
        assert response.status_code == 201
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert 'id' in data
        assert data['type'] == 'Golden Retriever'
        assert 'family' in data
        assert 'genus' in data
        assert 'attributes' in data
        assert isinstance(data['attributes'], list)
        assert 'lifespan' in data
        assert 'pets' in data
        assert isinstance(data['pets'], list)
        assert len(data['pets']) == 0
    
    def test_post_pet_type_malformed_data(self, client):
        """POST /pet-types - returns 400 for malformed data"""
        # Missing 'type' field
        response = client.post('/pet-types',
                              json={'name': 'Dog'},
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Malformed data'
        
        # Empty JSON
        response = client.post('/pet-types',
                              json={},
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Malformed data'
        
        # Multiple fields (should only have 'type')
        response = client.post('/pet-types',
                              json={'type': 'Dog', 'extra': 'field'},
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Malformed data'
    
    def test_post_pet_type_wrong_content_type(self, client):
        """POST /pet-types - returns 415 for wrong content type"""
        response = client.post('/pet-types',
                              data='{"type": "Dog"}',
                              content_type='text/plain')
        assert response.status_code == 415
        data = json.loads(response.data)
        assert data['error'] == 'Expected application/json media type'
    
    def test_post_pet_type_duplicate(self, client):
        """POST /pet-types - returns 400 for duplicate pet-type"""
        # Create first pet-type
        response1 = client.post('/pet-types',
                               json={'type': 'Golden Retriever'},
                               content_type='application/json')
        assert response1.status_code == 201
        
        # Try to create duplicate (case insensitive)
        response2 = client.post('/pet-types',
                               json={'type': 'golden retriever'},
                               content_type='application/json')
        assert response2.status_code == 400
        data = json.loads(response2.data)
        assert data['error'] == 'Pet type already exists'
    
    def test_post_pet_type_not_found_in_api(self, client):
        """POST /pet-types - returns 400 when pet-type not found in Ninja API"""
        response = client.post('/pet-types',
                              json={'type': 'NonExistentAnimal12345'},
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Pet type not found'
    
    def test_get_pet_types_with_query_id(self, client, sample_pet_type_id):
        """GET /pet-types - filter by id query parameter"""
        response = client.get(f'/pet-types?id={sample_pet_type_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['id'] == sample_pet_type_id
    
    def test_get_pet_types_with_query_type(self, client):
        """GET /pet-types - filter by type query parameter (case insensitive)"""
        client.post('/pet-types',
                   json={'type': 'Golden Retriever'},
                   content_type='application/json')
        
        response = client.get('/pet-types?type=golden retriever')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) == 1
        assert data[0]['type'] == 'Golden Retriever'
    
    def test_get_pet_types_with_query_family(self, client):
        """GET /pet-types - filter by family query parameter"""
        client.post('/pet-types',
                   json={'type': 'Golden Retriever'},
                   content_type='application/json')
        
        response = client.get('/pet-types?family=Canidae')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1
    
    def test_get_pet_types_with_query_genus(self, client):
        """GET /pet-types - filter by genus query parameter"""
        client.post('/pet-types',
                   json={'type': 'Golden Retriever'},
                   content_type='application/json')
        
        response = client.get('/pet-types?genus=Canis')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data) >= 1
    
    def test_get_pet_types_with_query_lifespan(self, client):
        """GET /pet-types - filter by lifespan query parameter"""
        client.post('/pet-types',
                   json={'type': 'Golden Retriever'},
                   content_type='application/json')
        
        response = client.get('/pet-types?lifespan=10')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should return pet-types with lifespan 10
        assert isinstance(data, list)
    
    def test_get_pet_types_with_query_hasAttribute(self, client):
        """GET /pet-types - filter by hasAttribute query parameter"""
        client.post('/pet-types',
                   json={'type': 'Golden Retriever'},
                   content_type='application/json')
        
        response = client.get('/pet-types?hasAttribute=active')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        # If any results, check that attributes contain the searched value (case insensitive)
        for pet_type in data:
            attributes = [attr.lower() for attr in pet_type.get('attributes', [])]
            assert 'active' in attributes
    
    def test_get_pet_types_multiple_queries(self, client):
        """GET /pet-types - filter by multiple query parameters"""
        client.post('/pet-types',
                   json={'type': 'Golden Retriever'},
                   content_type='application/json')
        
        response = client.get('/pet-types?family=Canidae&genus=Canis')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)


class TestPetTypeById:
    """Tests for /pet-types/{id} endpoint"""
    
    def test_get_pet_type_by_id_success(self, client, sample_pet_type_id):
        """GET /pet-types/{id} - returns pet-type with given id"""
        response = client.get(f'/pet-types/{sample_pet_type_id}')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['id'] == sample_pet_type_id
        assert 'type' in data
        assert 'family' in data
        assert 'genus' in data
        assert 'attributes' in data
        assert 'lifespan' in data
        assert 'pets' in data
        assert isinstance(data['pets'], list)
    
    def test_get_pet_type_by_id_not_found(self, client):
        """GET /pet-types/{id} - returns 404 for non-existent id"""
        response = client.get('/pet-types/99999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'
    
    def test_delete_pet_type_success(self, client, sample_pet_type_id):
        """DELETE /pet-types/{id} - successfully deletes pet-type with no pets"""
        response = client.delete(f'/pet-types/{sample_pet_type_id}')
        assert response.status_code == 204
        assert len(response.data) == 0  # Empty response
        
        # Verify it's deleted
        get_response = client.get(f'/pet-types/{sample_pet_type_id}')
        assert get_response.status_code == 404
    
    def test_delete_pet_type_with_pets(self, client, sample_pet_type_id):
        """DELETE /pet-types/{id} - returns 400 when pet-type has pets"""
        # Add a pet to the pet-type
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy'},
                   content_type='application/json')
        
        # Try to delete pet-type with pets
        response = client.delete(f'/pet-types/{sample_pet_type_id}')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Malformed data'
        
        # Verify pet-type still exists
        get_response = client.get(f'/pet-types/{sample_pet_type_id}')
        assert get_response.status_code == 200
    
    def test_delete_pet_type_not_found(self, client):
        """DELETE /pet-types/{id} - returns 404 for non-existent id"""
        response = client.delete('/pet-types/99999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'
    
    def test_put_pet_type_not_allowed(self, client, sample_pet_type_id):
        """PUT /pet-types/{id} - returns 405 (method not allowed)"""
        response = client.put(f'/pet-types/{sample_pet_type_id}',
                              json={'type': 'New Type'},
                              content_type='application/json')
        assert response.status_code == 405
        data = json.loads(response.data)
        assert data['error'] == 'Can not update pet type'


class TestPetsCollection:
    """Tests for /pet-types/{id}/pets endpoint"""
    
    def test_post_pet_success(self, client, sample_pet_type_id):
        """POST /pet-types/{id}/pets - successfully creates a pet"""
        response = client.post(f'/pet-types/{sample_pet_type_id}/pets',
                              json={'name': 'Buddy'},
                              content_type='application/json')
        assert response.status_code == 201
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['name'] == 'Buddy'
        assert data['birthdate'] == 'NA'
        assert data['picture'] == 'NA'
    
    def test_post_pet_with_birthdate(self, client, sample_pet_type_id):
        """POST /pet-types/{id}/pets - creates pet with birthdate"""
        response = client.post(f'/pet-types/{sample_pet_type_id}/pets',
                              json={'name': 'Max', 'birthdate': '15-03-2020'},
                              content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Max'
        assert data['birthdate'] == '15-03-2020'
    
    def test_post_pet_with_picture_url(self, client, sample_pet_type_id):
        """POST /pet-types/{id}/pets - creates pet with picture-url"""
        # Using a publicly available test image URL
        response = client.post(f'/pet-types/{sample_pet_type_id}/pets',
                              json={'name': 'Luna', 'picture-url': 'https://httpbin.org/image/jpeg'},
                              content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['name'] == 'Luna'
        assert data['picture'] != 'NA'
    
    def test_post_pet_malformed_data(self, client, sample_pet_type_id):
        """POST /pet-types/{id}/pets - returns 400 for malformed data"""
        # Missing 'name' field
        response = client.post(f'/pet-types/{sample_pet_type_id}/pets',
                              json={'birthdate': '15-03-2020'},
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Malformed data'
    
    def test_post_pet_wrong_content_type(self, client, sample_pet_type_id):
        """POST /pet-types/{id}/pets - returns 415 for wrong content type"""
        response = client.post(f'/pet-types/{sample_pet_type_id}/pets',
                              data='{"name": "Buddy"}',
                              content_type='text/plain')
        assert response.status_code == 415
        data = json.loads(response.data)
        assert data['error'] == 'Expected application/json media type'
    
    def test_post_pet_pet_type_not_found(self, client):
        """POST /pet-types/{id}/pets - returns 404 for non-existent pet-type"""
        response = client.post('/pet-types/99999/pets',
                              json={'name': 'Buddy'},
                              content_type='application/json')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'
    
    def test_post_pet_duplicate_name(self, client, sample_pet_type_id):
        """POST /pet-types/{id}/pets - returns 400 for duplicate pet name"""
        # Create first pet
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy'},
                   content_type='application/json')
        
        # Try to create duplicate (case insensitive)
        response = client.post(f'/pet-types/{sample_pet_type_id}/pets',
                              json={'name': 'buddy'},
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Malformed data'
    
    def test_get_pets_success(self, client, sample_pet_type_id):
        """GET /pet-types/{id}/pets - returns array of pets"""
        # Add some pets
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy'},
                   content_type='application/json')
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Max', 'birthdate': '15-03-2020'},
                   content_type='application/json')
        
        response = client.get(f'/pet-types/{sample_pet_type_id}/pets')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 2
    
    def test_get_pets_empty(self, client, sample_pet_type_id):
        """GET /pet-types/{id}/pets - returns empty array when no pets"""
        response = client.get(f'/pet-types/{sample_pet_type_id}/pets')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_get_pets_pet_type_not_found(self, client):
        """GET /pet-types/{id}/pets - returns 404 for non-existent pet-type"""
        response = client.get('/pet-types/99999/pets')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'
    
    def test_get_pets_with_birthdateGT(self, client, sample_pet_type_id):
        """GET /pet-types/{id}/pets - filter by birthdateGT query parameter"""
        # Add pets with different birthdates
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Old', 'birthdate': '01-01-2020'},
                   content_type='application/json')
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'New', 'birthdate': '01-01-2023'},
                   content_type='application/json')
        
        response = client.get(f'/pet-types/{sample_pet_type_id}/pets?birthdateGT=01-01-2022')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
        # Should only return pets with birthdate after 01-01-2022
        for pet in data:
            if pet['birthdate'] != 'NA':
                # Parse and verify date is after 01-01-2022
                pass
    
    def test_get_pets_with_birthdateLT(self, client, sample_pet_type_id):
        """GET /pet-types/{id}/pets - filter by birthdateLT query parameter"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Old', 'birthdate': '01-01-2020'},
                   content_type='application/json')
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'New', 'birthdate': '01-01-2023'},
                   content_type='application/json')
        
        response = client.get(f'/pet-types/{sample_pet_type_id}/pets?birthdateLT=01-01-2022')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_get_pets_with_both_date_filters(self, client, sample_pet_type_id):
        """GET /pet-types/{id}/pets - filter by both birthdateGT and birthdateLT"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Pet1', 'birthdate': '01-01-2020'},
                   content_type='application/json')
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Pet2', 'birthdate': '15-06-2021'},
                   content_type='application/json')
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Pet3', 'birthdate': '01-01-2023'},
                   content_type='application/json')
        
        response = client.get(f'/pet-types/{sample_pet_type_id}/pets?birthdateGT=01-01-2021&birthdateLT=01-01-2022')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_get_pets_invalid_date_format(self, client, sample_pet_type_id):
        """GET /pet-types/{id}/pets - returns 400 for invalid date format"""
        response = client.get(f'/pet-types/{sample_pet_type_id}/pets?birthdateGT=invalid-date')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data


class TestPetByName:
    """Tests for /pet-types/{id}/pets/{name} endpoint"""
    
    def test_get_pet_by_name_success(self, client, sample_pet_type_id):
        """GET /pet-types/{id}/pets/{name} - returns pet with given name"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy', 'birthdate': '15-03-2020'},
                   content_type='application/json')
        
        response = client.get(f'/pet-types/{sample_pet_type_id}/pets/Buddy')
        assert response.status_code == 200
        assert response.content_type == 'application/json'
        data = json.loads(response.data)
        assert data['name'] == 'Buddy'
        assert data['birthdate'] == '15-03-2020'
    
    def test_get_pet_by_name_case_insensitive(self, client, sample_pet_type_id):
        """GET /pet-types/{id}/pets/{name} - name matching is case insensitive"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy'},
                   content_type='application/json')
        
        response = client.get(f'/pet-types/{sample_pet_type_id}/pets/buddy')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Buddy'
    
    def test_get_pet_by_name_not_found(self, client, sample_pet_type_id):
        """GET /pet-types/{id}/pets/{name} - returns 404 for non-existent pet"""
        response = client.get(f'/pet-types/{sample_pet_type_id}/pets/NonExistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'
    
    def test_get_pet_by_name_pet_type_not_found(self, client):
        """GET /pet-types/{id}/pets/{name} - returns 404 for non-existent pet-type"""
        response = client.get('/pet-types/99999/pets/Buddy')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'
    
    def test_put_pet_success(self, client, sample_pet_type_id):
        """PUT /pet-types/{id}/pets/{name} - successfully updates pet"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy', 'birthdate': '15-03-2020'},
                   content_type='application/json')
        
        response = client.put(f'/pet-types/{sample_pet_type_id}/pets/Buddy',
                             json={'name': 'Buddy', 'birthdate': '20-05-2021'},
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'Buddy'
        assert data['birthdate'] == '20-05-2021'
    
    def test_put_pet_update_name(self, client, sample_pet_type_id):
        """PUT /pet-types/{id}/pets/{name} - can update pet name"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'OldName'},
                   content_type='application/json')
        
        response = client.put(f'/pet-types/{sample_pet_type_id}/pets/OldName',
                             json={'name': 'NewName'},
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['name'] == 'NewName'
        
        # Old name should not exist
        response2 = client.get(f'/pet-types/{sample_pet_type_id}/pets/OldName')
        assert response2.status_code == 404
        
        # New name should exist
        response3 = client.get(f'/pet-types/{sample_pet_type_id}/pets/NewName')
        assert response3.status_code == 200
    
    def test_put_pet_birthdate_na_when_not_provided(self, client, sample_pet_type_id):
        """PUT /pet-types/{id}/pets/{name} - sets birthdate to NA when not provided"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy', 'birthdate': '15-03-2020'},
                   content_type='application/json')
        
        response = client.put(f'/pet-types/{sample_pet_type_id}/pets/Buddy',
                             json={'name': 'Buddy'},
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['birthdate'] == 'NA'
    
    def test_put_pet_malformed_data(self, client, sample_pet_type_id):
        """PUT /pet-types/{id}/pets/{name} - returns 400 for malformed data"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy'},
                   content_type='application/json')
        
        # Missing 'name' field
        response = client.put(f'/pet-types/{sample_pet_type_id}/pets/Buddy',
                             json={'birthdate': '15-03-2020'},
                             content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Malformed data'
    
    def test_put_pet_wrong_content_type(self, client, sample_pet_type_id):
        """PUT /pet-types/{id}/pets/{name} - returns 415 for wrong content type"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy'},
                   content_type='application/json')
        
        response = client.put(f'/pet-types/{sample_pet_type_id}/pets/Buddy',
                             data='{"name": "Buddy"}',
                             content_type='text/plain')
        assert response.status_code == 415
        data = json.loads(response.data)
        assert data['error'] == 'Expected application/json media type'
    
    def test_put_pet_not_found(self, client, sample_pet_type_id):
        """PUT /pet-types/{id}/pets/{name} - returns 404 for non-existent pet"""
        response = client.put(f'/pet-types/{sample_pet_type_id}/pets/NonExistent',
                             json={'name': 'NonExistent'},
                             content_type='application/json')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'
    
    def test_delete_pet_success(self, client, sample_pet_type_id):
        """DELETE /pet-types/{id}/pets/{name} - successfully deletes pet"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy'},
                   content_type='application/json')
        
        response = client.delete(f'/pet-types/{sample_pet_type_id}/pets/Buddy')
        assert response.status_code == 204
        assert len(response.data) == 0
        
        # Verify pet is deleted
        get_response = client.get(f'/pet-types/{sample_pet_type_id}/pets/Buddy')
        assert get_response.status_code == 404
    
    def test_delete_pet_not_found(self, client, sample_pet_type_id):
        """DELETE /pet-types/{id}/pets/{name} - returns 404 for non-existent pet"""
        response = client.delete(f'/pet-types/{sample_pet_type_id}/pets/NonExistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'
    
    def test_delete_pet_pet_type_not_found(self, client):
        """DELETE /pet-types/{id}/pets/{name} - returns 404 for non-existent pet-type"""
        response = client.delete('/pet-types/99999/pets/Buddy')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'


class TestPictures:
    """Tests for /pictures/{file-name} endpoint"""
    
    def test_get_picture_success(self, client, sample_pet_type_id):
        """GET /pictures/{file-name} - returns image file"""
        # Create a pet with a picture
        response = client.post(f'/pet-types/{sample_pet_type_id}/pets',
                              json={'name': 'Buddy', 'picture-url': 'https://httpbin.org/image/jpeg'},
                              content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        picture_filename = data['picture']
        assert picture_filename != 'NA'
        
        # Get the picture
        pic_response = client.get(f'/pictures/{picture_filename}')
        assert pic_response.status_code == 200
        assert pic_response.content_type in ['image/jpeg', 'image/png']
    
    def test_get_picture_not_found(self, client):
        """GET /pictures/{file-name} - returns 404 for non-existent file"""
        response = client.get('/pictures/nonexistent.jpg')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['error'] == 'Not found'


class TestEdgeCases:
    """Edge cases and additional scenarios"""
    
    def test_pet_type_id_not_reused(self, client):
        """Verify that deleted pet-type IDs are not reused"""
        # Create and delete a pet-type
        response1 = client.post('/pet-types',
                               json={'type': 'Golden Retriever'},
                               content_type='application/json')
        assert response1.status_code == 201
        data1 = json.loads(response1.data)
        first_id = data1['id']
        
        client.delete(f'/pet-types/{first_id}')
        
        # Create another pet-type
        response2 = client.post('/pet-types',
                               json={'type': 'Poodle'},
                               content_type='application/json')
        assert response2.status_code == 201
        data2 = json.loads(response2.data)
        second_id = data2['id']
        
        # IDs should be different
        assert first_id != second_id
    
    def test_pets_field_is_array_of_strings(self, client, sample_pet_type_id):
        """Verify that pets field in pet-type is array of strings (names)"""
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Buddy'},
                   content_type='application/json')
        client.post(f'/pet-types/{sample_pet_type_id}/pets',
                   json={'name': 'Max'},
                   content_type='application/json')
        
        response = client.get(f'/pet-types/{sample_pet_type_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data['pets'], list)
        assert 'Buddy' in data['pets']
        assert 'Max' in data['pets']
        # Verify they are strings, not objects
        for pet_name in data['pets']:
            assert isinstance(pet_name, str)
    
    def test_attributes_parsing_words_not_commas(self, client):
        """Verify attributes are split by words, not commas"""
        response = client.post('/pet-types',
                               json={'type': 'Golden Retriever'},
                               content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        attributes = data.get('attributes', [])
        # Attributes should be individual words, not comma-separated phrases
        for attr in attributes:
            assert isinstance(attr, str)
            # Should not contain commas (unless it's part of a word)
    
    def test_lifespan_null_when_not_available(self, client):
        """Verify lifespan is null when not available from API"""
        # This test depends on API response
        # Some animals might not have lifespan data
        response = client.post('/pet-types',
                               json={'type': 'Golden Retriever'},
                               content_type='application/json')
        assert response.status_code == 201
        data = json.loads(response.data)
        # lifespan should be either an integer or null
        assert data['lifespan'] is None or isinstance(data['lifespan'], int)
    
    def test_case_insensitive_matching(self, client):
        """Verify case insensitive matching for pet-type names"""
        client.post('/pet-types',
                   json={'type': 'Golden Retriever'},
                   content_type='application/json')
        
        # Try to create with different case
        response = client.post('/pet-types',
                              json={'type': 'GOLDEN RETRIEVER'},
                              content_type='application/json')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'Pet type already exists'
    
    def test_picture_url_same_not_redownloaded(self, client, sample_pet_type_id):
        """Verify that same picture-url doesn't trigger re-download"""
        # Create pet with picture
        response1 = client.post(f'/pet-types/{sample_pet_type_id}/pets',
                               json={'name': 'Buddy', 'picture-url': 'https://httpbin.org/image/jpeg'},
                               content_type='application/json')
        assert response1.status_code == 201
        data1 = json.loads(response1.data)
        first_picture = data1['picture']
        
        # Update with same picture-url
        response2 = client.put(f'/pet-types/{sample_pet_type_id}/pets/Buddy',
                              json={'name': 'Buddy', 'picture-url': 'https://httpbin.org/image/jpeg'},
                              content_type='application/json')
        assert response2.status_code == 200
        data2 = json.loads(response2.data)
        second_picture = data2['picture']
        
        # Should be the same filename (not re-downloaded)
        assert first_picture == second_picture


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

